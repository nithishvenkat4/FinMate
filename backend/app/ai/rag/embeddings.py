"""Embedding Provider Abstraction for FinMate RAG Architecture.

Supports:
- LocalTFIDFEmbeddingProvider (Offline, deterministic, sublinear TF-IDF vectors)
- ExternalEmbeddingProvider (OpenAI / Gemini embedding integration)
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Embeds a single query string into a vector."""
        pass

    @abstractmethod
    def embed_documents(self, docs: List[str]) -> List[List[float]]:
        """Embeds a batch of document strings into vectors."""
        pass


class LocalTFIDFEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic local embedding provider using normalized TF-IDF representations.

    Ensures FinMate runs completely offline without third-party API dependencies
    or subscription costs.
    """

    def __init__(self, ngram_range=(1, 2), max_features=3000):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            sublinear_tf=True,
            norm="l2"
        )
        self.is_fitted = False

    def fit(self, corpus: List[str]):
        """Fits the vocabulary and inverse document frequency weights."""
        self.vectorizer.fit(corpus)
        self.is_fitted = True

    def embed_text(self, text: str) -> List[float]:
        if not self.is_fitted:
            raise RuntimeError("Embedding provider has not been fitted on knowledge corpus.")
        vec = self.vectorizer.transform([text]).toarray()[0]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, docs: List[str]) -> List[List[float]]:
        if not self.is_fitted:
            raise RuntimeError("Embedding provider has not been fitted on knowledge corpus.")
        mat = self.vectorizer.transform(docs).toarray()
        normalized = []
        for row in mat:
            norm = np.linalg.norm(row)
            if norm > 0:
                row = row / norm
            normalized.append(row.tolist())
        return normalized
