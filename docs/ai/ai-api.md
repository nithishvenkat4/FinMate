# FinMate Phase 3 — AI REST API Reference

Master prefix: `/api/v1/ai`

---

## 1. Classify Transaction

Predicts category from description and basic attributes using supervised NLP (Calibrated LinearSVC).

- **Endpoint**: `POST /api/v1/ai/classify-transaction`
- **Request Body**:
  ```json
  {
    "description": "Swiggy dinner order",
    "amount": "450.00",
    "transaction_type": "expense"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "predicted_category": "Food",
    "confidence": 0.9841,
    "requires_user_confirmation": false,
    "contributing_tokens": ["swiggy", "dinner", "order"],
    "model_version": "TfidfCalibratedLinearSVC@v1.0",
    "confidence_threshold": 0.60
  }
  ```

---

## 2. Forecast Expenses

Projects next-month aggregate spending using autoregressive lagged signals and TimeSeriesSplit calibration.

- **Endpoint**: `POST /api/v1/ai/forecast-expenses`
- **Request Body**:
  ```json
  {
    "recent_lags": [36000.0, 34500.0, 33000.0],
    "forecast_month": 10
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "predicted_expense": 34500.0,
    "uncertainty_range": {
      "lower_bound": 31450.0,
      "upper_bound": 37550.0,
      "confidence_level": "90%",
      "margin": 3050.0
    },
    "features_used": {
      "lag_1": 36000.0,
      "lag_2": 34500.0,
      "lag_3": 33000.0,
      "rolling_avg_3": 34500.0,
      "forecast_month": 10
    },
    "model_version": "RidgeRegression@v1.0",
    "limitation_notice": "Forecast based on historical seasonal trends; does not anticipate unannounced one-off expenses."
  }
  ```

---

## 3. Anomaly Check

Assesses whether a transaction amount represents an unusual deviation from the category benchmark.

- **Endpoint**: `POST /api/v1/ai/anomaly-check`
- **Request Body**:
  ```json
  {
    "amount": "15000.00",
    "category": "Food",
    "is_weekend": false
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "is_unusual": true,
    "anomaly_score": -0.1824,
    "category": "Food",
    "amount": 15000.0,
    "ratio_to_benchmark": 33.33,
    "explanation": "Transaction amount (₹15,000.00) is 33.33x higher than standard benchmark for Food.",
    "classification_notice": "Anomaly flags denote statistical deviation from baseline, not confirmed fraud."
  }
  ```

---

## 4. Retrieve RAG Guidance

Direct semantic search over verified official regulatory guidelines.

- **Endpoint**: `POST /api/v1/ai/retrieve`
- **Request Body**:
  ```json
  {
    "query": "What is an emergency fund and where should I keep it?",
    "top_k": 2
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "query": "What is an emergency fund and where should I keep it?",
    "retrieved_chunks": [
      {
        "chunk_id": "emergency_fund_guide.md::chunk_1",
        "title": "Emergency Fund Sizing, Architecture, and Operational Rules",
        "organization": "National Institute of Securities Markets (NISM)",
        "reference_code": "NISM-CP-EMERGENCY-2025-03",
        "similarity_score": 0.4821,
        "text": "An emergency fund is a ring-fenced, highly liquid pool of money..."
      }
    ],
    "sources": [
      {
        "title": "Emergency Fund Sizing, Architecture, and Operational Rules",
        "organization": "National Institute of Securities Markets (NISM)",
        "reference_code": "NISM-CP-EMERGENCY-2025-03",
        "jurisdiction": "India"
      }
    ],
    "has_sufficient_evidence": true,
    "notice": null
  }
  ```

---

## 5. Ask FinMate (End-to-End Decision Support)

Full synthesis pipeline: Deterministic Facts $\rightarrow$ ML Forecast $\rightarrow$ RAG Retrieval $\rightarrow$ LLM Synthesis.

- **Endpoint**: `POST /api/v1/ai/ask`
- **Request Body**:
  ```json
  {
    "question": "Can I afford a ₹20,000 laptop next month?",
    "include_financial_context": true
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "question": "Can I afford a ₹20,000 laptop next month?",
    "deterministic_facts": {
      "monthly_income": "60,000.00",
      "monthly_expenses": "35,000.00",
      "net_savings": "25,000.00",
      "savings_rate": "41.67%",
      "active_goals": ["Higher Education (Target: ₹3,00,000.00, Saved: ₹1,20,000.00)"],
      "current_savings_reserve": "1,20,000.00"
    },
    "ml_forecast": {
      "predicted_expense": 34500.0,
      "uncertainty_range": {
        "lower_bound": 31450.0,
        "upper_bound": 37550.0,
        "confidence_level": "90%",
        "margin": 3050.0
      }
    },
    "rag_sources": [
      {
        "title": "Practical Budgeting Methodologies and Cashflow Allocation Models",
        "organization": "Financial Planning Standards India",
        "reference_code": "FPSB-IN-BUDGET-2025-01"
      }
    ],
    "ai_decision_support": {
      "summary": "You have an estimated monthly surplus of ₹25,000... Purchasing a ₹20,000 laptop is feasible using single-month cashflow surplus...",
      "key_factors": [
        "Monthly income stability (₹60,000)",
        "Active High Priority Goal: Higher Education (₹3,00,000 target)",
        "Sufficient liquid savings for baseline emergency reserves"
      ],
      "evidence_used": ["FPSB India 50/30/20 Discretionary Outlay Guideline"],
      "uncertainties": ["Discretionary utility and food spending may vary by ±10%"],
      "action_options": [
        "Option 1: Purchase outright from current month surplus without touching emergency funds.",
        "Option 2: Apply the 30-Day Waiting Rule to ensure purchase remains essential.",
        "Option 3: Split outlay across two monthly cycles to maintain goal savings rate."
      ],
      "user_decision_required": true,
      "provider": "mock (mock-reasoner-v1)"
    },
    "safety_notice": "Decision-Support Only: FinMate provides explainable guidance; you make the final decision."
  }
  ```

---

## 6. List Registered Models

- **Endpoint**: `GET /api/v1/ai/models`
- **Response (200 OK)**:
  Returns all model metadata, versions, algorithms, and evaluated metrics.
