import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config.logger import logger
from backend.config.settings import settings
from rag_pipeline.embeddings.embedding_generator import EmbeddingGenerator
from rag_pipeline.processors.document_processor import DocumentProcessor, RuleExtractor
from rag_pipeline.vectordb.vector_store import VectorStore


class RAGManager:
    """Manages the RAG pipeline for document processing and retrieval"""

    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.rule_extractor = RuleExtractor()
        self.embedding_generator = EmbeddingGenerator(
            model_name=settings.embedding_model
        )
        self.vector_store = VectorStore(
            dimension=self.embedding_generator.embedding_dim,
            db_path=settings.vector_db_path,
        )

    async def process_document(
        self, file_path: str, document_id: str, document_type: str
    ) -> Dict[str, Any]:
        """Process a document through the RAG pipeline"""
        logger.info(f"Processing document: {file_path}")

        try:
            # Process document
            doc_data = self.document_processor.process_document(file_path)

            # Extract rules and sanctions
            rules = self.rule_extractor.extract_rules(doc_data["cleaned_text"])
            sanctions = self.rule_extractor.extract_sanctions_list(
                doc_data["cleaned_text"]
            )

            # Generate embeddings for chunks
            chunks_with_embeddings = self.embedding_generator.process_chunks(
                doc_data["chunks"]
            )

            # Prepare documents for vector store
            vector_documents = []
            for i, chunk in enumerate(chunks_with_embeddings):
                vector_doc = {
                    "id": f"{document_id}_chunk_{i}",
                    "text": chunk["text"],
                    "embedding": chunk["embedding"],
                    "source": document_id,
                    "chunk_index": i,
                    "metadata": {
                        "document_type": document_type,
                        "file_name": doc_data["file_name"],
                        "processed_at": datetime.utcnow().isoformat(),
                    },
                }
                vector_documents.append(vector_doc)

            # Add to vector store
            added_count = self.vector_store.add_documents(vector_documents)
            self.vector_store.save()

            logger.info(f"Successfully processed document: {document_id}")

            return {
                "success": True,
                "document_id": document_id,
                "chunks_processed": added_count,
                "rules_extracted": rules,
                "sanctions_extracted": sanctions,
                "processing_stats": {
                    "total_words": doc_data["total_words"],
                    "num_chunks": doc_data["num_chunks"],
                    "rules_found": len(rules),
                    "sanctioned_countries": len(sanctions["countries"]),
                    "sanctioned_entities": len(sanctions["entities"]),
                },
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            return {"success": False, "document_id": document_id, "error": str(e)}

    async def query_documents(
        self, query: str, k: int = 5, document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query documents using semantic search"""
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_single_embedding(query)

        # Search with optional filter
        filter_metadata = {"document_type": document_type} if document_type else None
        results = self.vector_store.search(
            query_embedding, k=k, filter_metadata=filter_metadata
        )

        return results

    async def check_sanctions(self, name: str, country: str) -> Dict[str, Any]:
        """Check if a name or country is sanctioned"""
        # Query for sanctions related to the name
        name_query = f"sanctioned person {name} prohibited individual {name}"
        name_results = await self.query_documents(
            name_query, k=3, document_type="sanctions_list"
        )

        # Query for country sanctions
        country_query = f"sanctioned country {country} prohibited jurisdiction {country} blacklisted {country}"
        country_results = await self.query_documents(
            country_query, k=3, document_type="sanctions_list"
        )

        # Check if name or country appears in high-similarity results
        is_sanctioned = False
        reasons = []

        for result in name_results:
            if result["similarity"] > 0.7 and name.lower() in result["text"].lower():
                is_sanctioned = True
                reasons.append(
                    f"Name found in sanctions document: {result['metadata']['file_name']}"
                )

        for result in country_results:
            if result["similarity"] > 0.7 and country.lower() in result["text"].lower():
                is_sanctioned = True
                reasons.append(
                    f"Country found in sanctions document: {result['metadata']['file_name']}"
                )

        return {
            "is_sanctioned": is_sanctioned,
            "reasons": reasons,
            "confidence": max(
                [r["similarity"] for r in name_results + country_results], default=0.0
            ),
        }

    async def get_compliance_rules(self, rule_type: str) -> List[Dict[str, Any]]:
        """Get compliance rules by type"""
        # Query for specific rule type
        query = f"compliance rule {rule_type} limit requirement regulation"
        results = await self.query_documents(
            query, k=5, document_type="compliance_rules"
        )

        # Extract rules from results
        rules = []
        for result in results:
            # Extract rules from the chunk text
            extracted_rules = self.rule_extractor.extract_rules(result["text"])
            for rule in extracted_rules:
                if rule["rule_type"] == rule_type:
                    rules.append(
                        {
                            "rule_type": rule["rule_type"],
                            "rule_value": rule["rule_value"],
                            "source": result["metadata"]["file_name"],
                            "confidence": result["similarity"],
                        }
                    )

        return rules

    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks related to a document"""
        deleted_count = self.vector_store.delete_by_source(document_id)
        if deleted_count > 0:
            self.vector_store.save()
            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        return self.vector_store.get_stats()


# Singleton instance
rag_manager = RAGManager()
