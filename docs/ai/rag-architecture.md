# FinMate Phase 3 — RAG (Retrieval-Augmented Generation) Architecture

---

## 1. Purpose of RAG in FinMate

FinMate uses RAG to ground financial reasoning in **curated, verified, and authoritative regulatory and planning guidelines**, preventing the LLM from hallucinating financial rules or citing fictitious blog posts.

---

## 2. Curated Knowledge Base

Knowledge documents are stored in `backend/app/ai/rag/knowledge/`:

| Document | Authority / Organization | Reference Code | Core Topics |
| :--- | :--- | :--- | :--- |
| `rbi_financial_education.md` | Reserve Bank of India (RBI) | `RBI-FIDD-FL-2025-01` | Banking rights, DTI limits (40-50%), credit card interest trap, digital security, unauthorized transaction liability. |
| `sebi_investor_charter.md` | Securities and Exchange Board of India (SEBI) | `SEBI-OIAE-CHARTER-2025-02` | Investor rights, risk vs return, multi-asset diversification, avoiding speculative F&O, investment horizon suitability. |
| `budgeting_principles.md` | Financial Planning Standards India | `FPSB-IN-BUDGET-2025-01` | 50/30/20 budget framework, cash surplus rule, 30-day rule for major purchases, debt snowball vs avalanche. |
| `emergency_fund_guide.md` | National Institute of Securities Markets (NISM) | `NISM-CP-EMERGENCY-2025-03` | Emergency reserve sizing (3-6 months), liquid parking, qualified emergencies vs discretionary misuse. |
| `inflation_and_compounding.md` | National Centre for Financial Education (NCFE) | `NCFE-ED-INFLATION-2025-04` | CPI inflation, real vs nominal returns, compound interest, Rule of 72, early compounding horizon. |

---

## 3. Document Chunking & Indexing

1. **Metadata Preservation**: The markdown parser extracts frontmatter metadata (`title`, `organization`, `reference_code`, `topic`, `jurisdiction`).
2. **Semantic Chunking**: Sections are partitioned along markdown header boundaries (`##`, `###`) into 500–600 character semantic chunks.
3. **Embedding Vectorization**:
   - `LocalTFIDFEmbeddingProvider`: Fits normalized sublinear TF-IDF vectors across the entire knowledge base. Zero external API cost, deterministic, and instant ($< 1$ ms).
4. **In-Memory Cosine Vector Store**:
   - Computes normalized vector dot products.
   - Operates identically in memory during testing, locally in SQLite fallback, or in PostgreSQL without requiring external extensions.

---

## 4. Semantic Retrieval Pipeline

When a user query is received:
1. The query string is normalized and embedded into a query vector $\vec{q}$.
2. The vector store computes cosine similarity against all indexed chunk vectors:
   $$\text{similarity}(\vec{q}, \vec{d}_i) = \frac{\vec{q} \cdot \vec{d}_i}{\|\vec{q}\| \|\vec{d}_i\|}$$
3. The top-$k$ nearest chunks ($k=3$) are ranked.
4. Chunks with similarity score $< 0.04$ are pruned as non-relevant.
5. If no chunk meets the threshold, the system flags `has_sufficient_evidence = false`.

---

## 5. Empirical Benchmark Results

Evaluated against `data/evaluation/rag_eval.json` (15 benchmark queries):
- **Hit Rate @ 1**: 93.3% (14/15)
- **Hit Rate @ 3**: 93.3% (14/15)
- **Mean Reciprocal Rank (MRR)**: 0.9333
- **Average Retrieval Latency**: 0.95 ms
- **Citation Attribution Accuracy**: 100%
