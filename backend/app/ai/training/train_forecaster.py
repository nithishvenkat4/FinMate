"""Training and Time-Aware Evaluation Script for Monthly Expense Forecasting.

Academic Requirement (CIT 19MAM54):
- Time-aware validation using TimeSeriesSplit (No future leakage)
- Model comparison: Moving Average Baseline vs Ridge Regression vs Random Forest Regressor
- Metrics: MAE, RMSE, R²
- Uncertainty and residual modeling
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

from app.ai.models.forecaster import (
    FEATURE_COLUMNS,
    MovingAverageBaselineForecaster,
    build_ridge_forecaster,
    build_random_forest_forecaster,
    evaluate_forecaster_time_series,
    evaluate_holdout_set
)
from app.ai.registry.registry import ModelRegistry, save_artifact

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_FILE = os.path.join(BASE_DIR, "data", "training", "expenses_monthly_train.csv")
EVAL_FILE = os.path.join(BASE_DIR, "data", "evaluation", "expenses_monthly_eval.csv")


def load_forecasting_data(filepath: str):
    X = []
    y = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            feats = [
                float(row["lag_1"]),
                float(row["lag_2"]),
                float(row["lag_3"]),
                float(row["rolling_avg_3"]),
                float(row["month_num"]),
            ]
            X.append(feats)
            y.append(float(row["total_expense"]))
    return np.array(X), np.array(y)


def train_and_evaluate_forecasters():
    print("=" * 70)
    print("TRAINING & EVALUATION: MONTHLY EXPENSE FORECASTING")
    print("=" * 70)

    X_train, y_train = load_forecasting_data(TRAIN_FILE)
    X_eval, y_eval = load_forecasting_data(EVAL_FILE)

    print(f"Historical Training Observations: {len(X_train)} months")
    print(f"Chronological Future Holdout Test: {len(X_eval)} months")
    print(f"Features: {', '.join(FEATURE_COLUMNS)}")
    print("-" * 70)

    registry = ModelRegistry()

    # 1. Baseline: 3-month Moving Average
    print("[1/3] Evaluating 3-Month Moving Average Baseline...")
    baseline = MovingAverageBaselineForecaster()
    cv_baseline = evaluate_forecaster_time_series(baseline, X_train, y_train, n_splits=3)
    holdout_baseline = evaluate_holdout_set(baseline, X_train, y_train, X_eval, y_eval)
    metrics_baseline = {**cv_baseline, **holdout_baseline}
    print(f"  Baseline -> CV MAE: INR {cv_baseline['cv_mae']:.2f} | Holdout MAE: INR {holdout_baseline['holdout_mae']:.2f} | R2: {holdout_baseline['holdout_r2']:.4f}")
    registry.register_model(
        task="expense_forecasting",
        model_name="MovingAverageBaseline",
        version="v1.0",
        algorithm="RollingAverage(window=3)",
        hyperparameters={"window": 3},
        metrics=metrics_baseline,
        is_selected=False,
        is_baseline=True,
        notes="Simple 3-month moving average persistence benchmark"
    )

    # 2. Model A: Ridge Regression
    print("[2/3] Fitting & Evaluating Model A (Ridge Regression with L2 Penalty)...")
    model_ridge = build_ridge_forecaster()
    cv_ridge = evaluate_forecaster_time_series(model_ridge, X_train, y_train, n_splits=3)
    # Refit on full training data
    model_ridge.fit(X_train, y_train)
    holdout_ridge = evaluate_holdout_set(model_ridge, X_train, y_train, X_eval, y_eval)
    metrics_ridge = {**cv_ridge, **holdout_ridge}
    print(f"  Ridge Regression -> CV MAE: INR {cv_ridge['cv_mae']:.2f} | Holdout MAE: INR {holdout_ridge['holdout_mae']:.2f} | R2: {holdout_ridge['holdout_r2']:.4f}")
    save_artifact(model_ridge, "forecaster_ridge.joblib")
    registry.register_model(
        task="expense_forecasting",
        model_name="RidgeRegression",
        version="v1.0",
        algorithm="Ridge(alpha=1.0)",
        hyperparameters={"alpha": 1.0, "fit_intercept": True},
        metrics=metrics_ridge,
        is_selected=False,
        is_baseline=False,
        artifact_path="forecaster_ridge.joblib",
        notes="L2 regularized linear autoregressive model on lagged features"
    )

    # 3. Model B: Random Forest Regressor
    print("[3/3] Fitting & Evaluating Model B (Random Forest Regressor)...")
    model_rf = build_random_forest_forecaster()
    cv_rf = evaluate_forecaster_time_series(model_rf, X_train, y_train, n_splits=3)
    model_rf.fit(X_train, y_train)
    holdout_rf = evaluate_holdout_set(model_rf, X_train, y_train, X_eval, y_eval)
    metrics_rf = {**cv_rf, **holdout_rf}
    print(f"  Random Forest -> CV MAE: INR {cv_rf['cv_mae']:.2f} | Holdout MAE: INR {holdout_rf['holdout_mae']:.2f} | R2: {holdout_rf['holdout_r2']:.4f}")
    save_artifact(model_rf, "forecaster_rf.joblib")

    # Select champion based on holdout MAE (lower rupee error is better)
    if holdout_ridge["holdout_mae"] <= holdout_rf["holdout_mae"]:
        champion_model = model_ridge
        champion_artifact = "forecaster_champion.joblib"
        save_artifact(model_ridge, champion_artifact)
        ridge_selected = True
        rf_selected = False
        print(f"\n[+] Champion Selected: Ridge Regression (Holdout MAE: INR {holdout_ridge['holdout_mae']:.2f})")
    else:
        champion_model = model_rf
        champion_artifact = "forecaster_champion.joblib"
        save_artifact(model_rf, champion_artifact)
        ridge_selected = False
        rf_selected = True
        print(f"\n[+] Champion Selected: Random Forest Regressor (Holdout MAE: INR {holdout_rf['holdout_mae']:.2f})")

    # Update selected status in registry
    registry.register_model(
        task="expense_forecasting",
        model_name="RidgeRegression",
        version="v1.0",
        algorithm="Ridge(alpha=1.0)",
        hyperparameters={"alpha": 1.0, "fit_intercept": True},
        metrics=metrics_ridge,
        is_selected=ridge_selected,
        is_baseline=False,
        artifact_path="forecaster_ridge.joblib",
        notes="L2 regularized linear autoregressive model"
    )
    registry.register_model(
        task="expense_forecasting",
        model_name="RandomForestRegressor",
        version="v1.0",
        algorithm="RandomForestRegressor(n_estimators=50, max_depth=5)",
        hyperparameters={"n_estimators": 50, "max_depth": 5, "random_state": 42},
        metrics=metrics_rf,
        is_selected=rf_selected,
        is_baseline=False,
        artifact_path="forecaster_rf.joblib",
        notes="Non-linear tree ensemble capturing complex seasonal patterns"
    )

    print("=" * 70)
    print("Forecasting training completed and recorded to registry.")
    print("=" * 70)


if __name__ == "__main__":
    train_and_evaluate_forecasters()
