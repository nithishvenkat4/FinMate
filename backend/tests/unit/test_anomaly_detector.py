"""Unit tests for Transaction Anomaly Detector."""

import pytest
import numpy as np
from app.ai.models.anomaly import (
    build_anomaly_detector,
    evaluate_transaction_anomaly,
    extract_anomaly_features
)


def test_extract_anomaly_features():
    feats = extract_anomaly_features(amount=4500.0, category="Food", is_weekend=False)
    assert feats.shape == (1, 3)
    assert feats[0][0] == 4500.0
    assert feats[0][1] == 10.0  # 4500 / benchmark(450)
    assert feats[0][2] == 0.0


def test_anomaly_detection_normal_vs_extreme():
    detector = build_anomaly_detector(contamination=0.05)
    # Train on 20 normal food transactions around ₹300 - ₹600
    normal_amounts = np.random.uniform(250.0, 600.0, 50)
    X_train = np.array([
        extract_anomaly_features(a, "Food", False)[0]
        for a in normal_amounts
    ])
    detector.fit(X_train)

    # Test normal transaction
    res_normal = evaluate_transaction_anomaly(detector, amount=400.0, category="Food")
    assert res_normal["is_unusual"] is False
    assert "within expected" in res_normal["explanation"]

    # Test extreme outlier transaction (e.g. ₹55,000 for Food)
    res_outlier = evaluate_transaction_anomaly(detector, amount=55000.0, category="Food")
    assert res_outlier["is_unusual"] is True
    assert res_outlier["ratio_to_benchmark"] > 10.0
    assert "higher than standard" in res_outlier["explanation"]
