# FinMate — Phase 3 Completion Report: AI Models & Intelligence

**Project**: FinMate – Personal Financial Decision Agent  
**Academic Context**: Coimbatore Institute of Technology — Department of Computing (AI & ML)  
**Course**: 19MAM54 — AI Systems Engineering  
**Module**: Phase 3 — AI Models & Intelligence  
**Date**: September 2026  
**Status**: Completed & Empirically Verified  

---

## 1. Executive Summary & Objectives

Phase 3 established the first **real AI intelligence layer** of the FinMate decision-support system, fully satisfying the academic syllabus requirements of 19MAM54:
- Real Machine Learning models for Transaction Categorization and Expense Forecasting.
- Comparative modeling studies benchmarking ML algorithms against established baselines.
- Real empirical evaluation metrics calculated on independent held-out datasets (Zero Fake AI).
- Natural Language Processing (NLP) text normalization and scikit-learn zero-leakage pipelines.
- Curated Retrieval-Augmented Generation (RAG) knowledge base covering official guidelines from RBI, SEBI, and budgeting authorities with 93.3% benchmark accuracy.
- Pluggable LLM abstraction layer with strict prompt hierarchy, prompt-injection defense, privacy sanitization, and deterministic fallbacks.
- REST APIs (`/api/v1/ai/*`) and interactive frontend workspace with live classification lab, forecasting studio, and model benchmark cards.
- Complete regression safety: 67/67 automated tests passing.

---

## 2. AI Architecture & Layer Separation

```
                    ┌─────────────────────────┐
                    │      USER / CLIENT      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    FinMate Frontend     │
                    │   (React + Vite + TS)   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   FastAPI Master API    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
         ┌─────────────────────┐   ┌─────────────────────┐
         │ Deterministic Layer │   │ AI Intelligence Hub │
         │  (AnalyticsService  │   │     (AIService)     │
         │   & Decimal Math)   │   └──────────┬──────────┘
         └─────────────────────┘              │
                     ┌────────────────────────┼────────────────────────┐
                     ▼                        ▼                        ▼
          ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
          │      ML Models      │  │     NLP / LLM       │  │     RAG Engine      │
          │  - Calibrated SVC   │  │  - Text Normalizer  │  │  - RBI/SEBI Chunks  │
          │  - Ridge Forecaster │  │  - Prompt Guardrail │  │  - Cosine Index     │
          │  - Isolation Forest │  │  - Mock / Ext LLMs  │  │  - Source Citations │
          └─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

---

## 3. Machine Learning Models, Baselines & Comparisons

### 3.1 Task 1: Transaction Category Classification (Supervised NLP)
- **Dataset**: 1,248 training and 312 evaluation samples across 12 balanced categories.
- **Results**:
  - *Keyword Baseline*: 63.78% Accuracy | 0.6833 Macro F1
  - *TF-IDF + Logistic Regression*: 97.76% Accuracy | 0.9796 Macro F1
  - *TF-IDF + Calibrated LinearSVC (Champion)*: **98.40% Accuracy | 0.9849 Macro F1**
- **Confidence Calibration**: LinearSVC Platt probability scaling; low-confidence gating ($< 0.60$) triggers human confirmation flag.

### 3.2 Task 2: Monthly Expense Forecasting (Time-Aware Regression)
- **Dataset**: 33 historical months training (2022–2024), 12 future months holdout (2025).
- **Leakage Prevention**: Strictly lagged features ($\text{lag}_1, \text{lag}_2, \text{lag}_3, \text{rolling\_3m}$); evaluated using `TimeSeriesSplit` (no lookahead bias).
- **Results**:
  - *3-Month Moving Average Baseline*: Holdout MAE ₹4,430.22 | $R^2: -0.4729$
  - *Ridge Regression ($\alpha=1.0$) (Champion)*: **Holdout MAE ₹3,369.93 | $R^2: 0.1872$** (24% error reduction)
  - *Random Forest Regressor*: Holdout MAE ₹3,470.49 | $R^2: 0.0732$
- **Uncertainty Bounds**: Cleanly rounded point estimates ($\pm ₹50$) with a 90% confidence statistical margin ($\pm 1.645\sigma$).

### 3.3 Task 3: Transaction Anomaly Detection (Unsupervised)
- **Algorithm**: `IsolationForest(n_estimators=100, contamination=0.04)`.
- **Result**: 1,198 inliers and 50 statistical outliers identified on baseline personal transaction distributions.
- **Non-Accusatory Language**: Uses *"unusual transaction"* or *"statistical spending deviation"* rather than *"fraud"*.

---

## 4. NLP & Text Preprocessing

- Implementation in `app.ai.nlp.preprocessor`:
  - Uniform casing, whitespace compaction.
  - Non-ASCII currency symbol handling (`₹`, `INR`, `Rs.` converted to `" inr "`).
  - Delimiter standardization for `UPI/xxx/123` and `POS`.
  - Encapsulated in scikit-learn `TextNormalizer` to guarantee zero train-test leakage.

---

## 5. RAG Knowledge Base & Retrieval Benchmarks

- **Curated Knowledge Documents**:
  1. `rbi_financial_education.md` (RBI Guidelines: DTI 40-50%, digital safety, liability limits)
  2. `sebi_investor_charter.md` (SEBI Guidelines: Multi-asset diversification, horizon suitability)
  3. `budgeting_principles.md` (FPSB India: 50/30/20 rule, cash surplus rule, 30-day waiting rule)
  4. `emergency_fund_guide.md` (NISM Guide: 3-6 months reserves, tiered parking)
  5. `inflation_and_compounding.md` (NCFE India: Real returns, Rule of 72, compounding horizon)
- **Vector Index**: In-memory Cosine Vector Store with sublinear TF-IDF embeddings.
- **Empirical RAG Benchmark (against 15 queries in `rag_eval.json`)**:
  - **Hit Rate @ 1**: 93.3% (14/15)
  - **Hit Rate @ 3**: 93.3% (14/15)
  - **Mean Reciprocal Rank (MRR)**: 0.9333
  - **Average Retrieval Latency**: 0.95 ms
  - **Source Citation Accuracy**: 100%

---

## 6. LLM Abstraction Layer & Safety Guardrails

1. **Provider Decoupling**:
   - `MockLLMProvider`: 100% deterministic, offline-capable, zero API cost.
   - `OpenAILLMProvider` & `GeminiLLMProvider`: Activated when environment API keys are configured.
2. **Authority Hierarchy**:
   $$\text{SYSTEM RULES} > \text{APPLICATION RULES} > \text{USER QUESTION} > \text{RETRIEVED SOURCES}$$
3. **Prompt Injection Defense**:
   - Untrusted delimiters: `<untrusted_user_input>` and `<untrusted_retrieved_evidence>`.
   - Rejection patterns for jailbreak commands, administrative overrides, and unauthorized monetary commands.
4. **Privacy Sanitization**: Strips credentials, API keys, passwords, bank account numbers, UPI PINs, and national IDs.
5. **Deterministic Fallbacks**: Automatic fallback to backend calculations on LLM timeouts or HTTP errors.

---

## 7. Model Registry & Metadata

- Lightweight JSON Model Registry maintained in `app/ai/registry/model_registry.json`.
- Tracks dataset hashes, hyperparameters, empirical metrics, champion selection flags, and artifact links.
- Serialized artifacts stored in `app/ai/artifacts/*.joblib`.

---

## 8. Verification & Acceptance Criteria Review

| Criterion | Requirement | Status | Verification Detail |
| :--- | :--- | :--- | :--- |
| **Supervised ML Models** | Classify transactions & compare against baseline | **Passed** | LinearSVC (98.4% Acc, 0.9849 F1) beats baseline (63.8%) |
| **Forecasting Prototype** | Chronological TimeSeriesSplit validation | **Passed** | Ridge MAE (₹3,369.93) beats baseline (₹4,430.22) |
| **Zero Fake AI** | Real empirical metrics; no hardcoded confidence | **Passed** | 100% generated from actual test runs; documented in registry |
| **NLP Pipeline** | Clean text, handle financial markers, zero leakage | **Passed** | `TextNormalizer` in scikit-learn Pipeline |
| **RAG Knowledge Base** | Curated official Indian financial documents | **Passed** | 5 official documents, 93.3% Hit Rate @ 3 on benchmark |
| **LLM Provider Abstraction**| Safe offline mock mode + pluggable external LLM | **Passed** | `MockLLMProvider` verified; graceful fallback active |
| **AI REST APIs** | Prediction, forecast, anomaly, ask, retrieve, models | **Passed** | 6 endpoints operational under `/api/v1/ai/*` |
| **Frontend Workspace** | Interactive Decision Support, Classifier, Studio | **Passed** | Built and verified (`npm run build` 0 errors) |
| **Regression Safety** | All Phase 0–2 tests must pass | **Passed** | **67/67 automated tests passing** in 1.98s |
| **Human-in-the-Loop** | Final financial decision remains with user | **Passed** | Explicit confirmation buttons; non-autonomous boundary |

---

## 9. Phase 4 Readiness & Service Decoupling

Phase 3 concludes with clean, stateless service abstractions prepared for Phase 4 multi-agent orchestration:
1. `FinancialAnalyticsService`: Authoritative Decimal accounting calculations.
2. `MLPredictionService`: Transaction classification, expense forecasting, and anomaly scoring.
3. `NLPService`: Financial text cleaning and token extraction.
4. `RAGService`: Semantic retrieval over regulatory knowledge base.
5. `LLMService`: Natural language synthesis, prompt injection defense, and fallback recovery.

> [!IMPORTANT]
> **Strict Phase 4 Boundary Preserved**:  
> No autonomous agents (Transaction Agent, Budget Agent, Goal Agent, Orchestrator) or autonomous tool loops were implemented in Phase 3. The architecture cleanly awaits Phase 4.
