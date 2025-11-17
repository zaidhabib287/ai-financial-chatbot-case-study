import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np


class VectorStore:
    """FAISS-based vector store for document embeddings"""

    def __init__(
        self,
        dimension: int = 384,  # Default for all-MiniLM-L6-v2
        index_type: str = "Flat",
        db_path: Optional[str] = None,
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.db_path = db_path or "./data/vectordb"

        # Create directory if it doesn't exist
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

        # Initialize FAISS index
        if index_type == "Flat":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "IVF":
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        # Metadata storage
        self.metadata = []
        self.id_to_index = {}

        # Load existing index if available
        self.load()

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Add documents with embeddings to the vector store"""
        if not documents:
            return 0

        # Extract embeddings and metadata
        embeddings = []
        for doc in documents:
            if "embedding" in doc:
                embeddings.append(doc["embedding"])

                # Store metadata
                metadata = {
                    "id": doc.get("id", str(len(self.metadata))),
                    "text": doc.get("text", ""),
                    "source": doc.get("source", ""),
                    "chunk_index": doc.get("chunk_index", 0),
                    "metadata": doc.get("metadata", {}),
                }

                self.id_to_index[metadata["id"]] = len(self.metadata)
                self.metadata.append(metadata)

        if embeddings:
            embeddings_array = np.array(embeddings).astype("float32")

            # Train index if needed (for IVF)
            if self.index_type == "IVF" and not self.index.is_trained:
                self.index.train(embeddings_array)

            # Add to index
            self.index.add(embeddings_array)

        return len(embeddings)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return []

        # Ensure query embedding is the right format
        query_embedding = np.array([query_embedding]).astype("float32")

        # Search
        distances, indices = self.index.search(
            query_embedding, min(k, self.index.ntotal)
        )

        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                result = {
                    "rank": i + 1,
                    "distance": float(dist),
                    "similarity": float(
                        1 / (1 + dist)
                    ),  # Convert distance to similarity
                    **self.metadata[idx],
                }

                # Apply filters if provided
                if filter_metadata:
                    match = all(
                        result.get(key) == value
                        for key, value in filter_metadata.items()
                    )
                    if not match:
                        continue

                results.append(result)

        return results

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        if doc_id in self.id_to_index:
            idx = self.id_to_index[doc_id]
            return self.metadata[idx]
        return None

    def delete_by_source(self, source: str) -> int:
        """Delete all documents from a specific source"""
        # This is a simple implementation - for production, consider more efficient approaches
        indices_to_keep = []
        new_metadata = []
        deleted_count = 0

        for i, meta in enumerate(self.metadata):
            if meta.get("source") != source:
                indices_to_keep.append(i)
                new_metadata.append(meta)
            else:
                deleted_count += 1

        if deleted_count > 0:
            # Rebuild index with remaining vectors
            if indices_to_keep:
                # Get vectors to keep
                vectors = []
                for i in indices_to_keep:
                    vectors.append(self.index.reconstruct(i))

                # Clear and rebuild index
                self.index.reset()
                vectors_array = np.array(vectors).astype("float32")

                if self.index_type == "IVF" and not self.index.is_trained:
                    self.index.train(vectors_array)

                self.index.add(vectors_array)
            else:
                self.index.reset()

            # Update metadata
            self.metadata = new_metadata
            self.id_to_index = {meta["id"]: i for i, meta in enumerate(self.metadata)}

        return deleted_count

    def save(self):
        """Save index and metadata to disk"""
        # Save FAISS index
        index_path = os.path.join(self.db_path, "index.faiss")
        faiss.write_index(self.index, index_path)

        # Save metadata
        metadata_path = os.path.join(self.db_path, "metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump(
                {
                    "metadata": self.metadata,
                    "id_to_index": self.id_to_index,
                    "dimension": self.dimension,
                    "index_type": self.index_type,
                },
                f,
            )

    def load(self) -> bool:
        """Load index and metadata from disk"""
        index_path = os.path.join(self.db_path, "index.faiss")
        metadata_path = os.path.join(self.db_path, "metadata.pkl")

        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_path)

                # Load metadata
                with open(metadata_path, "rb") as f:
                    data = pickle.load(f)
                    self.metadata = data["metadata"]
                    self.id_to_index = data["id_to_index"]
                    self.dimension = data["dimension"]
                    self.index_type = data["index_type"]

                return True
            except Exception as e:
                print(f"Error loading vector store: {e}")
                return False

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "total_documents": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metadata_count": len(self.metadata),
            "unique_sources": len(set(m.get("source", "") for m in self.metadata)),
        }
