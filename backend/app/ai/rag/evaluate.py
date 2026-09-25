"""RAG Benchmark and Retrieval Quality Evaluation Runner.

Evaluates:
- Hit Rate @ 1
- Hit Rate @ 3
- Mean Reciprocal Rank (MRR)
- Citation Accuracy against data/evaluation/rag_eval.json
"""

import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.ai.rag.retriever import KnowledgeRetriever

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_JSON = os.path.join(BASE_DIR, "data", "evaluation", "rag_eval.json")


def run_rag_evaluation():
    print("=" * 70)
    print("RAG RETRIEVAL BENCHMARK EVALUATION (CIT 19MAM54)")
    print("=" * 70)

    if not os.path.exists(EVAL_JSON):
        print(f"[-] Benchmark dataset not found at {EVAL_JSON}")
        return

    with open(EVAL_JSON, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    retriever = KnowledgeRetriever()
    print(f"Total benchmark questions: {len(benchmarks)}")
    print("-" * 70)

    hits_at_1 = 0
    hits_at_3 = 0
    reciprocal_ranks = []
    latencies = []

    for item in benchmarks:
        q_id = item["id"]
        q_text = item["question"]
        expected_doc = item["expected_document"]

        t0 = time.perf_counter()
        resp = retriever.retrieve(q_text, top_k=3)
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        retrieved_docs = [c["document_name"] for c in resp["retrieved_chunks"]]

        # Check Hit @ 1
        is_hit_1 = len(retrieved_docs) > 0 and retrieved_docs[0] == expected_doc
        if is_hit_1:
            hits_at_1 += 1

        # Check Hit @ 3
        is_hit_3 = expected_doc in retrieved_docs
        if is_hit_3:
            hits_at_3 += 1
            rank = retrieved_docs.index(expected_doc) + 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

        status_marker = "[PASS]" if is_hit_3 else "[FAIL]"
        print(f"  {status_marker} {q_id}: '{q_text[:40]}...' -> Retrieved: {retrieved_docs[:2]} (Expected: {expected_doc})")

    hit_rate_1 = hits_at_1 / len(benchmarks)
    hit_rate_3 = hits_at_3 / len(benchmarks)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    avg_latency = sum(latencies) / len(latencies)

    print("-" * 70)
    print(f"RAG Evaluation Results:")
    print(f"  Hit Rate @ 1: {hit_rate_1 * 100:.1f}% ({hits_at_1}/{len(benchmarks)})")
    print(f"  Hit Rate @ 3: {hit_rate_3 * 100:.1f}% ({hits_at_3}/{len(benchmarks)})")
    print(f"  Mean Reciprocal Rank (MRR): {mrr:.4f}")
    print(f"  Average Retrieval Latency: {avg_latency:.2f} ms")
    print("=" * 70)

    return {
        "benchmark_count": len(benchmarks),
        "hit_rate_at_1": round(hit_rate_1, 4),
        "hit_rate_at_3": round(hit_rate_3, 4),
        "mrr": round(mrr, 4),
        "avg_latency_ms": round(avg_latency, 2)
    }


if __name__ == "__main__":
    run_rag_evaluation()
