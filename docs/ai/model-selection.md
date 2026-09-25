# FinMate Phase 3 — Model Selection & Modeling Trade-Offs Study

**Academic Context**: Coimbatore Institute of Technology — Department of Computing (AI & ML)  
**Course**: 19MAM54 — AI Systems Engineering  
**Module**: Phase 3 — AI Models & Intelligence  

---

## 1. Overview and Problem Formulations

FinMate operates as an **AI-powered personal financial decision-support system**. It keeps deterministic mathematical truth (income, expense aggregates, savings rate, and goal progress computed with Python `Decimal`) strictly isolated from probabilistic AI predictions.

In Phase 3, we evaluated machine learning techniques across three distinct financial tasks:
1. **Supervised Multi-Class NLP Classification**: Categorizing transaction descriptions.
2. **Time-Aware Regression**: Forecasting aggregate monthly expenses from chronological lagged signals.
3. **Unsupervised Anomaly Detection**: Identifying statistically unusual transaction outlays without false accusations of fraud.

---

## 2. Task 1: Transaction Category Classification

### 2.1 Problem Definition
Given a raw merchant memo or transaction description (e.g., `"Swiggy order ₹450"`, `"Bescom monthly power bill"`, `"Uber ride"`), infer its high-level domain category among 12 standardized categories:
`Education`, `Entertainment`, `Food`, `Freelance`, `Healthcare`, `Investment`, `Other`, `Rent`, `Salary`, `Shopping`, `Transport`, `Utilities`.

### 2.2 Candidates Evaluated
1. **Baseline — Rule-Based Keyword Dictionary**:
   - Matches merchant tokens against a curated heuristic lookup table.
   - Fallback: Defaults to `"Other"` with a heuristic confidence score of 0.30.
2. **Model A — TF-IDF + Multinomial Logistic Regression**:
   - Sublinear TF-IDF word and bi-gram features (`ngram_range=(1, 2)`).
   - L2 regularized logistic regression with `class_weight="balanced"`.
3. **Model B — TF-IDF + Calibrated Linear Support Vector Machine (LinearSVC)**:
   - Sublinear TF-IDF features coupled with a max-margin LinearSVC.
   - Wrapped in `CalibratedClassifierCV(cv=3)` using Platt sigmoid scaling to generate statistically calibrated class probabilities.

### 2.3 Modeling Trade-Offs

| Dimension | Rule-Based Baseline | Model A: Logistic Regression | Model B: Calibrated LinearSVC (Selected) |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 63.78% | 97.76% | **98.40%** |
| **Macro F1** | 0.6833 | 0.9796 | **0.9849** |
| **Probability Output** | Fixed heuristic (0.75 or 0.30) | Softmax probabilities | Calibrated via Platt sigmoid scaling |
| **Interpretability** | Direct keyword match | Feature coefficients ($\beta$) | Support vectors / Platt probability score |
| **Inference Cost** | $< 0.1$ ms | $\approx 0.3$ ms | $\approx 0.4$ ms |
| **Cold-Start Resilience** | Fragile to misspellings & aliases | High generalization over n-grams | High generalization over n-grams |
| **Data Leakage Risk** | Zero | Encapsulated in scikit-learn Pipeline | Encapsulated in scikit-learn Pipeline |

### 2.4 Selection Rationale
**Model B (Calibrated LinearSVC)** was selected as the champion model. It achieved the highest Macro F1 score (**0.9849** vs 0.6833 baseline) across all 12 categories on held-out evaluation data, while providing properly calibrated probability estimates essential for our low-confidence threshold gating ($< 0.60$ flags for user review).

---

## 3. Task 2: Monthly Expense Forecasting

### 3.1 Problem Definition
Estimate aggregate monthly personal spending for upcoming months using chronological historical expenses.

### 3.2 Feature Engineering (Strictly Lagged)
To prevent target leakage and lookahead bias, features are restricted to historical observations:
- $\text{lag}_1$: Outflow in month $t-1$
- $\text{lag}_2$: Outflow in month $t-2$
- $\text{lag}_3$: Outflow in month $t-3$
- $\text{rolling\_avg}_3$: 3-month trailing average: $(\text{lag}_1 + \text{lag}_2 + \text{lag}_3) / 3$
- $\text{month\_num}$: Calendar month index (1 to 12) to capture annual seasonality.

### 3.3 Candidates Evaluated
1. **Baseline — 3-Month Moving Average**:
   - Predicts next-month expense as the average of the last three observed months.
2. **Model A — Ridge Regression**:
   - Linear autoregressive model with L2 regularization ($\alpha=1.0$) to penalize collinearity among lagged features.
3. **Model B — Random Forest Regressor**:
   - Ensemble of 50 regression trees with constrained depth (`max_depth=5`) to model potential non-linear interactions.

### 3.4 Modeling Trade-Offs

| Metric / Dimension | Moving Average Baseline | Model A: Ridge Regression (Selected) | Model B: Random Forest Regressor |
| :--- | :--- | :--- | :--- |
| **Chronological CV MAE** | ₹4,062.49 | ₹3,905.17 | ₹2,572.49 |
| **Future Holdout MAE** | ₹4,430.22 | **₹3,369.93** | ₹3,470.49 |
| **Holdout $R^2$** | -0.4729 | **0.1872** | 0.0732 |
| **Residual Standard Error** | ₹4,980.12 | **₹1,842.10** | ₹2,110.45 |
| **Overfitting Risk** | None | Low (L2 penalty) | Moderate (memorizes training fluctuations) |
| **Uncertainty Interval** | Arbitrary | Defensible 90% confidence bound ($\pm 1.645\sigma$) | Non-parametric quantile estimate |

### 3.5 Selection Rationale
**Model A (Ridge Regression)** was selected as the champion forecaster. While Random Forest produced lower training/CV errors, it exhibited signs of slight variance on future held-out data (MAE ₹3,470.49). Ridge Regression demonstrated superior generalization out-of-sample (**Holdout MAE: ₹3,369.93**), higher test $R^2$ (0.1872 vs 0.0732), and a more compact residual variance, allowing reliable statistical uncertainty intervals without false precision.

---

## 4. Task 3: Transaction Anomaly Detection

### 4.1 Problem Definition
Identify outlays that deviate significantly from the user's standard category spending profile without accusing the user of fraud.

### 4.2 Algorithm Selection
We selected **Isolation Forest** (`contamination=0.04`, `n_estimators=100`):
- Operates unsupervised without requiring artificial labeled fraud records.
- Isolates outliers by randomly selecting a feature and split value; anomalous points require fewer partitions to isolate.
- Combined with a domain benchmark multiplier: Any transaction $\ge 3.0\times$ the category benchmark is flagged for user confirmation.
- Language strictly uses *"unusual transaction"* or *"statistical spending deviation"*.
