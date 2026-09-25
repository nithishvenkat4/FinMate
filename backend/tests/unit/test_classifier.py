"""Unit tests for Transaction Category Classification models."""

import pytest
from app.ai.models.classifier import (
    KeywordBaselineClassifier,
    build_logistic_regression_pipeline,
    predict_with_confidence,
    evaluate_classifier
)


def test_keyword_baseline():
    clf = KeywordBaselineClassifier()
    cat, conf = clf.predict_one("Swiggy lunch delivery")
    assert cat == "Food"
    assert conf >= 0.70

    cat_unk, conf_unk = clf.predict_one("completely unknown merchant xyz")
    assert cat_unk == "Other"
    assert conf_unk <= 0.40


def test_logistic_regression_training_and_eval():
    pipe = build_logistic_regression_pipeline()
    train_texts = [
        "Swiggy lunch order", "Zomato dinner", "McDonalds burger",
        "Uber cab ride", "Ola auto commute", "Metro card recharge",
        "Amazon retail shopping", "Flipkart purchase", "Myntra clothes"
    ]
    train_labels = [
        "Food", "Food", "Food",
        "Transport", "Transport", "Transport",
        "Shopping", "Shopping", "Shopping"
    ]
    pipe.fit(train_texts, train_labels)

    eval_texts = ["Zomato meal", "Uber cab", "Amazon dress"]
    eval_labels = ["Food", "Transport", "Shopping"]

    metrics = evaluate_classifier(pipe, eval_texts, eval_labels, ["Food", "Shopping", "Transport"])
    assert metrics["accuracy"] >= 0.66
    assert "macro_f1" in metrics
    assert "confusion_matrix" in metrics


def test_predict_with_confidence_and_thresholding():
    pipe = build_logistic_regression_pipeline()
    pipe.fit(
        ["Swiggy meal", "Uber ride", "Amazon shirt"],
        ["Food", "Transport", "Shopping"]
    )
    # High confidence expected for near-exact match
    res_high = predict_with_confidence(pipe, "Swiggy dinner meal", confidence_threshold=0.50)
    assert res_high["predicted_category"] == "Food"
    assert res_high["confidence"] > 0.30
    assert isinstance(res_high["contributing_tokens"], list)

    # Low confidence handling test
    res_low = predict_with_confidence(pipe, "Random unknown entity 999", confidence_threshold=0.99)
    assert res_low["requires_user_confirmation"] is True
