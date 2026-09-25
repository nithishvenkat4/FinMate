# Model Card: Transaction Category Classifier

## 1. Model Details
- **Model Name**: `TfidfCalibratedLinearSVC`
- **Version**: `v1.0`
- **Task**: Supervised Multi-class NLP Text Classification (12 categories)
- **Algorithm**: Linear Support Vector Classifier (`LinearSVC(C=1.0)`) calibrated with Platt sigmoid scaling via `CalibratedClassifierCV(cv=3)`.
- **Feature Representation**: Sublinear TF-IDF word and character n-grams (`ngram_range=(1, 2)`, `max_features=2500`).
- **Owner / Module**: `app.ai.models.classifier`

## 2. Intended Use
- **Primary Intended Use**: Suggest appropriate category tags for incoming user transactions (e.g. Swiggy $\rightarrow$ Food, Uber $\rightarrow$ Transport).
- **Non-Intended Use**: Autonomous tax deduction filing, automated ledger accounting without user review, or legally binding expense audits.

## 3. Training & Evaluation Data
- **Training Dataset**: `data/training/transactions_train.csv` (1,248 labeled synthetic examples reflecting Indian merchant names, UPI memos, and banking statements).
- **Evaluation Dataset**: `data/evaluation/transactions_eval.csv` (312 held-out test transactions across 12 balanced categories).

## 4. Measured Performance
- **Accuracy**: 98.40%
- **Macro Precision**: 0.9854
- **Macro Recall**: 0.9841
- **Macro F1**: 0.9849
- **Weighted F1**: 0.9839

## 5. Decision Safeguards & Limitations
- **Confidence Gating**: If calibrated confidence $< 0.60$, the system flags `requires_user_confirmation = true`.
- **Known Failure Modes**: Extremely vague strings (e.g. `"Misc Payment"`, `"Transfer 1"`) default to `"Other"` with low confidence.
- **Human-in-the-Loop**: Users can override any category suggestion at any time.
