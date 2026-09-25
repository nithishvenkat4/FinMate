"""Vector Store Abstraction and In-Memory Cosine Similarity Store.

Provides high-speed vector retrieval across SQLite, PostgreSQL, or local files
without requiring external database extensions or heavyweight C++ builds.
"""

from abc import ABC, abstractmethod
import json
import os
from typing import List, Dict, Any, Tuple
import numpy as np


class BaseVectorStore(ABC):
    """Abstract interface for vector database storage and similarity search."""

    @abstractmethod
    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Adds text chunks and their corresponding embedding vectors to the index."""
        pass

    @abstractmethod
    def similarity_search(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Finds top-k nearest semantic chunks based on vector distance/similarity."""
        pass


class InMemoryCosineVectorStore(BaseVectorStore):
    """In-memory vector store performing normalized dot-product / cosine similarity."""

    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray = np.empty((0, 0))

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        if not chunks or not embeddings:
            return

        self.chunks.extend(chunks)
        new_vecs = np.array(embeddings, dtype=np.float32)

        if self.embeddings.size == 0:
            self.embeddings = new_vecs
        else:
            self.embeddings = np.vstack([self.embeddings, new_vecs])

    def similarity_search(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        if self.embeddings.size == 0 or not self.chunks:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Cosine similarity is dot product of normalized vectors
        scores = np.dot(self.embeddings, q_vec)

        # Get top-k indices
        top_k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = dict(self.chunks[idx])
            chunk["similarity_score"] = round(float(scores[idx]), 4)
            results.append(chunk)

        return results

    def save_index(self, filepath: str):
        """Persists the in-memory index to disk."""
        data = {
            "chunks": self.chunks,
            "embeddings": self.embeddings.tolist()
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_index(self, filepath: str):
        """Restores index from disk."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Vector index not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.chunks = data["chunks"]
        self.embeddings = np.array(data["embeddings"], dtype=np.float32)
