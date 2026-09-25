"""Semantic Knowledge Base Retriever for FinMate RAG Architecture."""

import os
from typing import List, Dict, Any, Optional
from app.ai.rag.chunker import load_knowledge_base_chunks
from app.ai.rag.embeddings import LocalTFIDFEmbeddingProvider
from app.ai.rag.store import InMemoryCosineVectorStore


DEFAULT_KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")


class KnowledgeRetriever:
    """Semantic Knowledge Retriever grounded in verified official financial guidelines."""

    def __init__(self, knowledge_dir: str = DEFAULT_KNOWLEDGE_DIR):
        self.knowledge_dir = knowledge_dir
        self.embedding_provider = LocalTFIDFEmbeddingProvider()
        self.vector_store = InMemoryCosineVectorStore()
        self.is_indexed = False
        self._build_index()

    def _build_index(self):
        """Indexes all curated markdown documents in the knowledge directory."""
        if not os.path.exists(self.knowledge_dir):
            return

        chunks = load_knowledge_base_chunks(self.knowledge_dir)
        if not chunks:
            return

        # Fit embedding provider on all chunk texts
        corpus = [c["text"] for c in chunks]
        self.embedding_provider.fit(corpus)

        # Generate vectors
        vectors = self.embedding_provider.embed_documents(corpus)

        # Populate vector store
        self.vector_store.add_documents(chunks, vectors)
        self.is_indexed = True

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_relevance_threshold: float = 0.04
    ) -> Dict[str, Any]:
        """Retrieves top-k relevant knowledge chunks with source citations and relevance gating."""
        if not self.is_indexed or not query or not query.strip():
            return {
                "query": query,
                "retrieved_chunks": [],
                "sources": [],
                "has_sufficient_evidence": False,
                "notice": "No relevant documents found or knowledge base is empty."
            }

        q_vec = self.embedding_provider.embed_text(query)
        results = self.vector_store.similarity_search(q_vec, top_k=top_k)

        # Filter out chunks with negligible similarity
        qualified = [r for r in results if r.get("similarity_score", 0.0) >= min_relevance_threshold]

        sources = []
        for c in qualified:
            src = {
                "title": c.get("title"),
                "organization": c.get("organization"),
                "reference_code": c.get("reference_code"),
                "topic": c.get("topic"),
                "jurisdiction": c.get("jurisdiction"),
                "document_name": c.get("document_name")
            }
            if src not in sources:
                sources.append(src)

        has_sufficient_evidence = len(qualified) > 0

        return {
            "query": query,
            "retrieved_chunks": qualified,
            "sources": sources,
            "has_sufficient_evidence": has_sufficient_evidence,
            "notice": None if has_sufficient_evidence else "Insufficient retrieved evidence for this question."
        }
