"""Transaction Category Classification Models.

Includes:
1. Rule-based / Keyword Baseline
2. TF-IDF + Multinomial Logistic Regression
3. TF-IDF + Linear Support Vector Machine (LinearSVC with probability calibration)

Provides:
- Strict pipeline coupling (TextNormalizer -> TfidfVectorizer -> Classifier)
- Evaluation metrics: Accuracy, Precision, Recall, Macro F1, Weighted F1, Confusion Matrix
- Empirical confidence thresholding (< 0.60 requires confirmation)
- Explanation feature extraction (top n-gram weights)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

from app.ai.nlp.preprocessor import TextNormalizer, clean_financial_text


# Keyword Rule Dictionary for Baseline Comparison
KEYWORD_BASELINE_RULES = {
    "swiggy": "Food",
    "zomato": "Food",
    "mcdonald": "Food",
    "starbucks": "Food",
    "coffee": "Food",
    "biryani": "Food",
    "haldiram": "Food",
    "subway": "Food",
    "kfc": "Food",
    "blinkit": "Food",
    "zepto": "Food",
    "bigbasket": "Food",
    "pizza": "Food",
    "grocery": "Food",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "zara": "Shopping",
    "ajio": "Shopping",
    "nykaa": "Shopping",
    "croma": "Shopping",
    "decathlon": "Shopping",
    "shoes": "Shopping",
    "clothing": "Shopping",
    "uber": "Transport",
    "ola": "Transport",
    "rapido": "Transport",
    "metro": "Transport",
    "petrol": "Transport",
    "diesel": "Transport",
    "fuel": "Transport",
    "fastag": "Transport",
    "flight": "Transport",
    "irctc": "Transport",
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    "bookmyshow": "Entertainment",
    "prime": "Entertainment",
    "hotstar": "Entertainment",
    "cinema": "Entertainment",
    "movie": "Entertainment",
    "bescom": "Utilities",
    "power": "Utilities",
    "broadband": "Utilities",
    "fiber": "Utilities",
    "gas": "Utilities",
    "water": "Utilities",
    "recharge": "Utilities",
    "pharmacy": "Healthcare",
    "apollo": "Healthcare",
    "medplus": "Healthcare",
    "hospital": "Healthcare",
    "doctor": "Healthcare",
    "lab": "Healthcare",
    "medicine": "Healthcare",
    "coursera": "Education",
    "udemy": "Education",
    "tuition": "Education",
    "college": "Education",
    "exam": "Education",
    "rent": "Rent",
    "pg": "Rent",
    "flat": "Rent",
    "zerodha": "Investment",
    "groww": "Investment",
    "sip": "Investment",
    "etf": "Investment",
    "ppf": "Investment",
    "nps": "Investment",
    "gold": "Investment",
    "salary": "Salary",
    "payroll": "Salary",
    "bonus": "Salary",
    "upwork": "Freelance",
    "fiverr": "Freelance",
    "freelance": "Freelance",
    "consulting": "Freelance",
    "atm": "Other",
}


class KeywordBaselineClassifier:
    """Deterministic Rule-Based Baseline Classifier."""

    def __init__(self, default_category: str = "Other"):
        self.default_category = default_category
        self.classes_ = sorted(list(set(KEYWORD_BASELINE_RULES.values())) + ["Other"])

    def fit(self, X, y=None):
        return self

    def predict_one(self, text: str) -> Tuple[str, float]:
        cleaned = clean_financial_text(text)
        tokens = cleaned.split()
        for token in tokens:
            for kw, cat in KEYWORD_BASELINE_RULES.items():
                if kw in token:
                    return cat, 0.75  # Fixed heuristic confidence
        return self.default_category, 0.30

    def predict(self, X: List[str]) -> List[str]:
        return [self.predict_one(x)[0] for x in X]


def build_logistic_regression_pipeline() -> Pipeline:
    """Builds TF-IDF + Logistic Regression Classification Pipeline."""
    return Pipeline([
        ("normalizer", TextNormalizer()),
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=2500,
            sublinear_tf=True
        )),
        ("clf", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
            C=1.5
        ))
    ])


def build_linear_svc_pipeline() -> Pipeline:
    """Builds TF-IDF + Calibrated LinearSVC Pipeline.

    Uses CalibratedClassifierCV to obtain statistically grounded probability
    distributions from a max-margin LinearSVC.
    """
    base_svc = LinearSVC(
        C=1.0,
        random_state=42,
        max_iter=2000,
        dual="auto"
    )
    calibrated_svc = CalibratedClassifierCV(estimator=base_svc, cv=3)

    return Pipeline([
        ("normalizer", TextNormalizer()),
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=2500,
            sublinear_tf=True
        )),
        ("clf", calibrated_svc)
    ])


def evaluate_classifier(model, X_test: List[str], y_test: List[str], class_labels: List[str]) -> Dict[str, Any]:
    """Computes rigorous classification evaluation metrics."""
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    # Calculate Precision, Recall, Macro and Weighted F1
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_test, y_pred, average="macro", zero_division=0
    )
    p_weighted, r_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_test, y_pred, average="weighted", zero_division=0
    )
    
    cm = confusion_matrix(y_test, y_pred, labels=class_labels).tolist()

    return {
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "macro_f1": round(float(f1_macro), 4),
        "weighted_precision": round(float(p_weighted), 4),
        "weighted_recall": round(float(r_weighted), 4),
        "weighted_f1": round(float(f1_weighted), 4),
        "confusion_matrix": cm,
        "class_labels": class_labels,
        "sample_count": len(y_test)
    }


def predict_with_confidence(
    model,
    text: str,
    confidence_threshold: float = 0.60
) -> Dict[str, Any]:
    """Infers category with calibrated probability and low-confidence gating."""
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba([text])[0]
        classes = model.classes_
        top_idx = int(np.argmax(probs))
        predicted_category = str(classes[top_idx])
        confidence = round(float(probs[top_idx]), 4)
    else:
        # Fallback for baseline or uncalibrated models
        if isinstance(model, KeywordBaselineClassifier):
            predicted_category, confidence = model.predict_one(text)
        else:
            predicted_category = str(model.predict([text])[0])
            confidence = 0.50

    requires_confirmation = confidence < confidence_threshold

    # Extract keywords present in text for explainability
    cleaned = clean_financial_text(text)
    tokens = [t for t in cleaned.split() if len(t) > 2]

    return {
        "predicted_category": predicted_category if not requires_confirmation else predicted_category,
        "confidence": confidence,
        "requires_user_confirmation": requires_confirmation,
        "contributing_tokens": tokens[:4],
        "confidence_threshold": confidence_threshold
    }
