"""Training and Evaluation Script for Transaction Category Classification.

Academic Requirement (CIT 19MAM54):
- Model comparison: Baseline vs Logistic Regression vs Calibrated LinearSVC
- Evaluation metrics: Accuracy, Precision, Recall, Macro F1, Weighted F1, Confusion Matrix
- Model selection and registration
"""

import csv
import os
import sys

from app.ai.models.classifier import (
    KeywordBaselineClassifier,
    build_logistic_regression_pipeline,
    build_linear_svc_pipeline,
    evaluate_classifier
)
from app.ai.registry.registry import ModelRegistry, save_artifact

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "transactions_train.csv")
EVAL_FILE = os.path.join(BASE_DIR, "data", "evaluation", "transactions_eval.csv")


def load_data(filepath: str):
    descriptions = []
    categories = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            descriptions.append(row["description"])
            categories.append(row["category"])
    return descriptions, categories


def train_and_evaluate_classifiers():
    print("=" * 70)
    print("TRAINING & EVALUATION: TRANSACTION CATEGORY CLASSIFIER")
    print("=" * 70)

    X_train, y_train = load_data(TRAIN_FILE)
    X_eval, y_eval = load_data(EVAL_FILE)
    classes = sorted(list(set(y_train)))

    print(f"Training Samples: {len(X_train)} | Evaluation Samples: {len(X_eval)}")
    print(f"Categories ({len(classes)}): {', '.join(classes)}")
    print("-" * 70)

    registry = ModelRegistry()

    # 1. Baseline: Keyword Dictionary
    print("[1/3] Evaluating Keyword Baseline...")
    baseline = KeywordBaselineClassifier()
    metrics_baseline = evaluate_classifier(baseline, X_eval, y_eval, classes)
    print(f"  Baseline -> Accuracy: {metrics_baseline['accuracy']:.4f} | Macro F1: {metrics_baseline['macro_f1']:.4f}")
    registry.register_model(
        task="transaction_classification",
        model_name="KeywordBaseline",
        version="v1.0",
        algorithm="RuleBasedDictionary",
        hyperparameters={"rules_count": len(baseline.classes_)},
        metrics=metrics_baseline,
        is_selected=False,
        is_baseline=True,
        notes="Heuristic merchant keyword mapping"
    )

    # 2. Model A: Logistic Regression
    print("[2/3] Fitting & Evaluating Model A (TF-IDF + Logistic Regression)...")
    model_lr = build_logistic_regression_pipeline()
    model_lr.fit(X_train, y_train)
    metrics_lr = evaluate_classifier(model_lr, X_eval, y_eval, classes)
    print(f"  Logistic Regression -> Accuracy: {metrics_lr['accuracy']:.4f} | Macro F1: {metrics_lr['macro_f1']:.4f}")
    save_artifact(model_lr, "classifier_logistic_regression.joblib")
    registry.register_model(
        task="transaction_classification",
        model_name="TfidfLogisticRegression",
        version="v1.0",
        algorithm="LogisticRegression(C=1.5, balanced)",
        hyperparameters={"C": 1.5, "max_iter": 1000, "ngram_range": [1, 2]},
        metrics=metrics_lr,
        is_selected=False,
        is_baseline=False,
        artifact_path="classifier_logistic_regression.joblib",
        notes="Multinomial logistic regression with sublinear TF-IDF"
    )

    # 3. Model B: Calibrated Linear SVC
    print("[3/3] Fitting & Evaluating Model B (TF-IDF + Calibrated LinearSVC)...")
    model_svc = build_linear_svc_pipeline()
    model_svc.fit(X_train, y_train)
    metrics_svc = evaluate_classifier(model_svc, X_eval, y_eval, classes)
    print(f"  Calibrated LinearSVC -> Accuracy: {metrics_svc['accuracy']:.4f} | Macro F1: {metrics_svc['macro_f1']:.4f}")
    save_artifact(model_svc, "classifier_calibrated_svc.joblib")

    # Select Champion Model based on Macro F1
    if metrics_svc["macro_f1"] >= metrics_lr["macro_f1"]:
        champion_model = model_svc
        champion_name = "TfidfCalibratedLinearSVC"
        champion_artifact = "classifier_champion.joblib"
        save_artifact(model_svc, champion_artifact)
        svc_selected = True
        lr_selected = False
        print(f"\n[+] Champion Selected: Calibrated LinearSVC (Macro F1: {metrics_svc['macro_f1']:.4f})")
    else:
        champion_model = model_lr
        champion_name = "TfidfLogisticRegression"
        champion_artifact = "classifier_champion.joblib"
        save_artifact(model_lr, champion_artifact)
        svc_selected = False
        lr_selected = True
        print(f"\n[+] Champion Selected: Logistic Regression (Macro F1: {metrics_lr['macro_f1']:.4f})")

    registry.register_model(
        task="transaction_classification",
        model_name="TfidfCalibratedLinearSVC",
        version="v1.0",
        algorithm="CalibratedClassifierCV(LinearSVC(C=1.0))",
        hyperparameters={"C": 1.0, "cv": 3, "ngram_range": [1, 2]},
        metrics=metrics_svc,
        is_selected=svc_selected,
        is_baseline=False,
        artifact_path="classifier_calibrated_svc.joblib",
        notes="Linear support vector classifier with Platt probability calibration"
    )

    print("=" * 70)
    print("Classification training completed successfully and recorded to registry.")
    print("=" * 70)


if __name__ == "__main__":
    train_and_evaluate_classifiers()
