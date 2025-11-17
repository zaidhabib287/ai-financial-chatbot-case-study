#!/usr/bin/env python
"""Test script for RAG pipeline functionality"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag_pipeline.embeddings.embedding_generator import EmbeddingGenerator
from rag_pipeline.processors.document_processor import DocumentProcessor, RuleExtractor
from rag_pipeline.vectordb.vector_store import VectorStore


def create_test_document():
    """Create a test compliance document"""
    test_doc_path = "./data/test_compliance.txt"

    test_content = """
    Financial Compliance Rules and Regulations

    1. Daily Transfer Limits
    The maximum daily transfer limit for individual customers is 1000 BHD (Bahraini Dinars).
    Corporate accounts may have a daily limit of up to 50000 BHD.

    2. Per-Transaction Limits
    Individual transactions are limited to 500 BHD per transaction.
    Transactions exceeding this amount require additional verification.

    3. Sanctioned Countries
    The following countries are currently under sanctions and transfers are prohibited:
    - North Korea
    - Iran
    - Syria
    - Cuba

    4. Prohibited Entities
    The following entities are sanctioned and no transactions should be processed:
    - ABC Trading Company
    - XYZ International Holdings
    - Test Sanctioned Person

    5. Compliance Requirements
    All transactions must be screened against the current sanctions list.
    Customer due diligence must be performed for transactions over 100 BHD.
    """

    os.makedirs(os.path.dirname(test_doc_path), exist_ok=True)
    with open(test_doc_path, "w") as f:
        f.write(test_content)

    return test_doc_path


async def test_document_processor():
    """Test document processing"""
    print("\n=== Testing Document Processor ===")

    # Create test document
    test_doc_path = create_test_document()

    processor = DocumentProcessor()
    result = processor.process_document(test_doc_path)

    print(f"✓ Document processed successfully")
    print(f"  Total words: {result['total_words']}")
    print(f"  Number of chunks: {result['num_chunks']}")
    print(f"  First chunk preview: {result['chunks'][0]['text'][:100]}...")

    # Test rule extraction
    extractor = RuleExtractor()
    rules = extractor.extract_rules(result["cleaned_text"])
    sanctions = extractor.extract_sanctions_list(result["cleaned_text"])

    print(f"\n✓ Rules extracted: {len(rules)}")
    for rule in rules:
        print(f"  - {rule['rule_type']}: {rule['rule_value']}")

    print(f"\n✓ Sanctions extracted:")
    print(f"  Countries: {sanctions['countries']}")
    print(f"  Entities: {sanctions['entities']}")

    return result


async def test_embeddings():
    """Test embedding generation"""
    print("\n=== Testing Embeddings ===")

    generator = EmbeddingGenerator()

    # Test single embedding
    test_text = "This is a test sentence for embedding generation."
    embedding = generator.generate_single_embedding(test_text)

    print(f"✓ Single embedding generated")
    print(f"  Embedding dimension: {len(embedding)}")
    print(f"  Embedding sample: {embedding[:5]}")

    # Test batch embeddings
    test_texts = [
        "Daily transfer limit is 1000 BHD",
        "Maximum transaction amount is 500 BHD",
        "North Korea is a sanctioned country",
    ]
    embeddings = generator.generate_embeddings(test_texts)

    print(f"\n✓ Batch embeddings generated")
    print(f"  Number of embeddings: {len(embeddings)}")
    print(f"  Shape: {embeddings.shape}")

    # Test similarity
    query = "What is the daily limit?"
    query_embedding = generator.generate_single_embedding(query)

    similarities = []
    for i, emb in enumerate(embeddings):
        sim = generator.calculate_similarity(query_embedding, emb)
        similarities.append((i, sim, test_texts[i]))

    similarities.sort(key=lambda x: x[1], reverse=True)

    print(f"\n✓ Similarity search results for: '{query}'")
    for idx, sim, text in similarities:
        print(f"  {sim:.3f}: {text}")


async def test_vector_store():
    """Test vector store operations"""
    print("\n=== Testing Vector Store ===")

    # Create vector store
    store = VectorStore(dimension=384)

    # Create test documents
    generator = EmbeddingGenerator()
    test_docs = [
        {
            "id": "doc1_chunk1",
            "text": "Daily transfer limit is 1000 BHD for individual customers",
            "source": "doc1",
            "metadata": {"document_type": "compliance_rules"},
        },
        {
            "id": "doc1_chunk2",
            "text": "Sanctioned countries include North Korea, Iran, and Syria",
            "source": "doc1",
            "metadata": {"document_type": "sanctions_list"},
        },
        {
            "id": "doc2_chunk1",
            "text": "Per transaction limit is 500 BHD",
            "source": "doc2",
            "metadata": {"document_type": "compliance_rules"},
        },
    ]

    # Generate embeddings
    for doc in test_docs:
        doc["embedding"] = generator.generate_single_embedding(doc["text"])

    # Add to store
    added = store.add_documents(test_docs)
    print(f"✓ Added {added} documents to vector store")

    # Test search
    query = "What are the transfer limits?"
    query_embedding = generator.generate_single_embedding(query)
    results = store.search(query_embedding, k=2)

    print(f"\n✓ Search results for: '{query}'")
    for result in results:
        print(f"  Rank {result['rank']}: {result['text'][:60]}...")
        print(f"    Similarity: {result['similarity']:.3f}")

    # Test filtered search
    results = store.search(
        query_embedding, k=2, filter_metadata={"document_type": "sanctions_list"}
    )
    print(f"\n✓ Filtered search (sanctions only): {len(results)} results")

    # Test stats
    stats = store.get_stats()
    print(f"\n✓ Vector store stats: {stats}")

    # Clean up
    os.makedirs("./data/vectordb", exist_ok=True)


async def main():
    """Run all RAG pipeline tests"""
    print("Testing RAG Pipeline Components...")

    # Test each component
    doc_result = await test_document_processor()
    await test_embeddings()
    await test_vector_store()

    print("\n✓ All RAG pipeline tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
