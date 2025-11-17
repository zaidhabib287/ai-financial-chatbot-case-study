import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import torch


class EmbeddingGenerator:
    """Generate embeddings for text chunks using Sentence Transformers"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not texts:
            return np.array([])
        
        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        
        return embeddings
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        return self.generate_embeddings([text])[0]
    
    def process_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process chunks and add embeddings"""
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i]
        
        return chunks
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        # Since embeddings are normalized, dot product equals cosine similarity
        return float(np.dot(embedding1, embedding2))
    
    def find_similar_texts(self, 
                          query_embedding: np.ndarray, 
                          text_embeddings: np.ndarray, 
                          top_k: int = 5,
                          threshold: float = 0.5) -> List[int]:
        """Find most similar texts based on embeddings"""
        # Calculate similarities
        similarities = np.dot(text_embeddings, query_embedding)
        
        # Get indices of top-k similar texts
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Filter by threshold
        filtered_indices = [
            idx for idx in top_indices 
            if similarities[idx] >= threshold
        ]
        
        return filtered_indices
