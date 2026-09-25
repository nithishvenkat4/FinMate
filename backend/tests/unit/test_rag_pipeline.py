"""Unit tests for RAG Chunker, Embedding Provider, Store, and Retriever."""

import pytest
import tempfile
import os

from app.ai.rag.chunker import chunk_document, parse_markdown_metadata
from app.ai.rag.embeddings import LocalTFIDFEmbeddingProvider
from app.ai.rag.store import InMemoryCosineVectorStore
from app.ai.rag.retriever import KnowledgeRetriever


SAMPLE_DOC = """# Test Document Title

**Document Metadata**:
- **Title**: Emergency Savings Guide
- **Organization**: National Finance Board
- **Reference Code**: NFB-001
- **Publication Date**: 2025-01-01
- **Topic**: Emergency Funds
- **Jurisdiction**: India

---

## 1. What is an Emergency Reserve
An emergency fund must cover 3 to 6 months of mandatory living expenses.
It protects households from unforeseen medical emergencies or sudden unemployment.

## 2. Liquid Parking
Do not invest emergency savings in volatile equity markets.
Keep reserves in high-interest savings accounts or sweep-in fixed deposits.
"""


def test_parse_markdown_metadata():
    meta, body = parse_markdown_metadata(SAMPLE_DOC)
    assert meta["title"] == "Emergency Savings Guide"
    assert meta["organization"] == "National Finance Board"
    assert meta["reference_code"] == "NFB-001"
    assert "What is an Emergency Reserve" in body


def test_chunk_document_tempfile():
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE_DOC)
        temp_path = f.name

    try:
        chunks = chunk_document(temp_path, target_chunk_size=200)
        assert len(chunks) >= 2
        assert chunks[0]["title"] == "Emergency Savings Guide"
        assert chunks[0]["organization"] == "National Finance Board"
        assert any("emergency" in c["text"].lower() for c in chunks)
    finally:
        os.remove(temp_path)


def test_vector_store_and_embedding_search():
    provider = LocalTFIDFEmbeddingProvider()
    store = InMemoryCosineVectorStore()

    corpus = [
        "An emergency reserve should cover 3 to 6 months of living expenses.",
        "Systematic investment plans SIP in equity mutual funds offer long-term compounding.",
        "Credit cards carry high interest rates up to 42 percent per annum."
    ]
    provider.fit(corpus)
    vectors = provider.embed_documents(corpus)

    chunks = [{"id": f"c_{i}", "text": text} for i, text in enumerate(corpus)]
    store.add_documents(chunks, vectors)

    # Search for emergency query
    q_vec = provider.embed_text("how much emergency money should I keep?")
    results = store.similarity_search(q_vec, top_k=1)
    assert len(results) == 1
    assert "emergency reserve" in results[0]["text"]
    assert results[0]["similarity_score"] > 0


def test_retriever_real_knowledge_base():
    retriever = KnowledgeRetriever()
    resp = retriever.retrieve("What is an emergency fund?", top_k=2)
    assert resp["has_sufficient_evidence"] is True
    assert len(resp["retrieved_chunks"]) > 0
    assert len(resp["sources"]) > 0
    assert any("emergency" in s["title"].lower() or "emergency" in s["topic"].lower() for s in resp["sources"])
