# Model Card: Transaction Anomaly Detector

## 1. Model Details
- **Model Name**: `IsolationForestAnomalyDetector`
- **Version**: `v1.0`
- **Task**: Unsupervised Outlier / Spending Irregularity Detection
- **Algorithm**: `IsolationForest(n_estimators=100, contamination=0.04)`
- **Features**: Amount, ratio to category baseline benchmark, weekend indicator.
- **Owner / Module**: `app.ai.models.anomaly`

## 2. Intended Use
- **Primary Intended Use**: Alert users to statistical spending anomalies within specific categories (e.g. ₹15,000 for Food).
- **Non-Intended Use**: Legal fraud forensics, anti-money laundering (AML) regulatory filing, or card blocking without human approval.

## 3. Training Data
- **Training Dataset**: 1,248 synthetic personal transactions across standard personal spending distributions.
- **Contamination Rate**: 4.0% (50 outliers identified during baseline training).

## 4. Decision Safeguards & Limitations
- **Non-Accusatory Terminology**: Uses *"unusual transaction"* or *"statistical spending deviation"* rather than *"fraud"*.
- **Benchmark Guardrail**: Transactions $\ge 3.0\times$ category benchmark automatically flag an advisory note.
