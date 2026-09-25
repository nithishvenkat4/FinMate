"""Master Training Orchestration Runner.

Runs:
1. Transaction Classification Training & Comparison
2. Monthly Expense Forecasting Training & Time-aware Validation
3. Transaction Anomaly Detector Training

Saves all serialized artifacts to app/ai/artifacts/ and updates app/ai/registry/model_registry.json.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.ai.training.train_classifier import train_and_evaluate_classifiers
from app.ai.training.train_forecaster import train_and_evaluate_forecasters
from app.ai.training.train_anomaly import train_anomaly_detector


def train_all():
    print("\n" + "#" * 80)
    print("STARTING COMPLETE FINMATE AI MODEL TRAINING & EVALUATION SUITE")
    print("#" * 80 + "\n")

    train_and_evaluate_classifiers()
    print("\n")
    train_and_evaluate_forecasters()
    print("\n")
    train_anomaly_detector()

    print("\n" + "#" * 80)
    print("ALL AI MODELS TRAINED, EVALUATED, AND REGISTERED TO REGISTRY")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    train_all()
