"""Transaction Anomaly Detection using Unsupervised Isolation Forest.

Features:
- Normalized transaction amount
- Category relative spending multiplier
- Weekend indicator

Safeguards:
- Language strictly uses 'unusual transaction' or 'spending irregularity' rather than 'fraud'.
- Explainable justification returned for any flagged transaction.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import IsolationForest


CATEGORY_BENCHMARKS = {
    "Food": 450.0,
    "Shopping": 1800.0,
    "Transport": 350.0,
    "Entertainment": 650.0,
    "Utilities": 1200.0,
    "Healthcare": 800.0,
    "Education": 1500.0,
    "Rent": 15000.0,
    "Investment": 5000.0,
    "Other": 1000.0,
}


def build_anomaly_detector(contamination: float = 0.05) -> IsolationForest:
    """Builds Isolation Forest model with designated contamination threshold."""
    return IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42
    )


def extract_anomaly_features(
    amount: float,
    category: str,
    is_weekend: bool = False
) -> np.ndarray:
    """Constructs numerical features for anomaly inference."""
    benchmark = CATEGORY_BENCHMARKS.get(category, 1000.0)
    ratio = amount / max(benchmark, 1.0)
    return np.array([[amount, ratio, 1.0 if is_weekend else 0.0]])


def evaluate_transaction_anomaly(
    model: IsolationForest,
    amount: float,
    category: str,
    is_weekend: bool = False
) -> Dict[str, Any]:
    """Infers anomaly score and generates plain-language decision support."""
    features = extract_anomaly_features(amount, category, is_weekend)
    benchmark = CATEGORY_BENCHMARKS.get(category, 1000.0)
    ratio = round(amount / max(benchmark, 1.0), 2)

    # In sklearn Isolation Forest:
    # predict returns -1 for outlier, 1 for inlier
    pred = model.predict(features)[0]
    # score_samples returns opposite of anomaly score (lower means more anomalous)
    raw_score = float(model.score_samples(features)[0])

    is_unusual = (pred == -1) or (ratio >= 3.0)

    if is_unusual:
        if ratio >= 2.5:
            reason = f"Transaction amount (₹{amount:,.2f}) is {ratio}x higher than standard benchmark for {category}."
        else:
            reason = f"Transaction amount (₹{amount:,.2f}) deviates significantly from standard {category} spending patterns."
    else:
        reason = f"Transaction is within expected spending ranges for {category}."

    return {
        "is_unusual": bool(is_unusual),
        "anomaly_score": round(raw_score, 4),
        "category": category,
        "amount": amount,
        "ratio_to_benchmark": ratio,
        "explanation": reason,
        "classification_notice": "Anomaly flags denote statistical deviation from baseline, not confirmed fraud."
    }
