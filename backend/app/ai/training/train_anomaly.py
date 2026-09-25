"""Training and Registration for Transaction Anomaly Detector.

Academic Context (CIT 19MAM54):
- Unsupervised learning using Isolation Forest
- Statistical outlier score modeling
- Decision support without fraudulent accusations
"""

import csv
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np

from app.ai.models.anomaly import (
    build_anomaly_detector,
    extract_anomaly_features
)
from app.ai.registry.registry import ModelRegistry, save_artifact

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "transactions_train.csv")


def train_anomaly_detector():
    print("=" * 70)
    print("TRAINING: TRANSACTION ANOMALY DETECTOR (ISOLATION FOREST)")
    print("=" * 70)

    feature_rows = []
    with open(TRAIN_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            amt = float(row["amount"])
            cat = row["category"]
            feats = extract_anomaly_features(amt, cat, is_weekend=False)[0]
            feature_rows.append(feats)

    X = np.array(feature_rows)
    print(f"Training on {len(X)} baseline transaction feature vectors...")

    detector = build_anomaly_detector(contamination=0.04)
    detector.fit(X)

    inliers = np.sum(detector.predict(X) == 1)
    outliers = np.sum(detector.predict(X) == -1)

    print(f"Fit complete: {inliers} inliers, {outliers} potential irregularities ({outliers/len(X)*100:.1f}%).")

    save_artifact(detector, "anomaly_detector.joblib")

    registry = ModelRegistry()
    registry.register_model(
        task="anomaly_detection",
        model_name="IsolationForestAnomalyDetector",
        version="v1.0",
        algorithm="IsolationForest(n_estimators=100, contamination=0.04)",
        hyperparameters={"n_estimators": 100, "contamination": 0.04, "random_state": 42},
        metrics={
            "training_samples": len(X),
            "inliers_count": int(inliers),
            "outliers_count": int(outliers),
            "contamination_rate": 0.04
        },
        is_selected=True,
        is_baseline=False,
        artifact_path="anomaly_detector.joblib",
        notes="Unsupervised Isolation Forest to detect statistical deviation in transaction amounts"
    )

    print("=" * 70)
    print("Anomaly detector trained and registered successfully.")
    print("=" * 70)


if __name__ == "__main__":
    train_anomaly_detector()
