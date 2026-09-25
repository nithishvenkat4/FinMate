"""Monthly Expense Forecasting Models and Time-Aware Validation.

Models:
1. Baseline: 3-Month Moving Average / Previous Period Persistence
2. Model A: Ridge Regression (L2 regularized linear lag model)
3. Model B: Random Forest Regressor

Features (Strictly lagged to eliminate future-data leakage):
- lag_1, lag_2, lag_3
- rolling_avg_3
- month_num (1 to 12)

Validation:
- TimeSeriesSplit (Chronological cross-validation, train precedes test)
- Metrics: MAE, RMSE, R²
- Uncertainty: Residual standard error interval (90% confidence range)
- Precision: Cleanly rounded rupee figures (No false precision)
"""

import math
from typing import Dict, List, Tuple, Any
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


FEATURE_COLUMNS = ["lag_1", "lag_2", "lag_3", "rolling_avg_3", "month_num"]


class MovingAverageBaselineForecaster:
    """Baseline forecaster using moving average of recent lags."""

    def __init__(self, window: int = 3):
        self.window = window

    def fit(self, X, y=None):
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        # X[:, 3] corresponds to rolling_avg_3
        return X[:, 3]


def build_ridge_forecaster() -> Ridge:
    """Builds Ridge regression forecaster with tuned L2 penalty."""
    return Ridge(alpha=1.0, random_state=42)


def build_random_forest_forecaster() -> RandomForestRegressor:
    """Builds Random Forest Regressor for non-linear monthly patterns."""
    return RandomForestRegressor(
        n_estimators=50,
        max_depth=5,
        random_state=42,
        min_samples_split=2
    )


def evaluate_forecaster_time_series(
    model,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 3
) -> Dict[str, Any]:
    """Evaluates forecaster strictly using chronological TimeSeriesSplit."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    mae_list = []
    rmse_list = []
    r2_list = []

    for train_idx, test_idx in tscv.split(X):
        X_train_cv, X_test_cv = X[train_idx], X[test_idx]
        y_train_cv, y_test_cv = y[train_idx], y[test_idx]

        if hasattr(model, "fit"):
            model.fit(X_train_cv, y_train_cv)

        preds = model.predict(X_test_cv)
        mae = mean_absolute_error(y_test_cv, preds)
        rmse = math.sqrt(mean_squared_error(y_test_cv, preds))
        r2 = r2_score(y_test_cv, preds)

        mae_list.append(mae)
        rmse_list.append(rmse)
        r2_list.append(r2)

    return {
        "cv_mae": round(float(np.mean(mae_list)), 2),
        "cv_rmse": round(float(np.mean(rmse_list)), 2),
        "cv_r2": round(float(np.mean(r2_list)), 4),
        "n_splits": n_splits
    }


def evaluate_holdout_set(
    model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_eval: np.ndarray,
    y_eval: np.ndarray
) -> Dict[str, Any]:
    """Fits on entire historical training dataset and evaluates on future holdout set."""
    if hasattr(model, "fit"):
        model.fit(X_train, y_train)

    preds = model.predict(X_eval)
    residuals = y_train - model.predict(X_train)
    residual_std = float(np.std(residuals))

    mae = mean_absolute_error(y_eval, preds)
    rmse = math.sqrt(mean_squared_error(y_eval, preds))
    r2 = r2_score(y_eval, preds)

    return {
        "holdout_mae": round(float(mae), 2),
        "holdout_rmse": round(float(rmse), 2),
        "holdout_r2": round(float(r2), 4),
        "residual_std": round(residual_std, 2),
        "eval_count": len(y_eval),
        "actual_vs_predicted": [
            {"actual": round(float(a), 2), "predicted": round(float(p), 2)}
            for a, p in zip(y_eval, preds)
        ]
    }


def forecast_next_period(
    model,
    recent_lags: List[float],
    next_month_num: int,
    residual_std: float = 1800.0
) -> Dict[str, Any]:
    """Generates next-month forecast with explicit uncertainty interval.

    Args:
        model: Trained regression model.
        recent_lags: [lag_1 (most recent), lag_2, lag_3].
        next_month_num: Calendar month index (1-12) for the forecast.
        residual_std: Estimated standard deviation of forecast residuals.

    Returns:
        Structured forecast with rounded point estimate and uncertainty band.
    """
    if len(recent_lags) < 3:
        return {
            "error": "Insufficient historical periods (minimum 3 required).",
            "predicted_expense": None
        }

    lag_1, lag_2, lag_3 = recent_lags[:3]
    rolling_3 = (lag_1 + lag_2 + lag_3) / 3.0

    features = np.array([[lag_1, lag_2, lag_3, rolling_3, next_month_num]])
    raw_pred = float(model.predict(features)[0])

    # Round to nearest 50 for clean reporting (no false precision like 34212.83)
    point_estimate = round(raw_pred / 50.0) * 50.0

    # 90% confidence interval: point_estimate +/- 1.645 * residual_std
    margin = round((1.645 * residual_std) / 50.0) * 50.0
    lower_bound = max(0.0, point_estimate - margin)
    upper_bound = point_estimate + margin

    return {
        "predicted_expense": point_estimate,
        "uncertainty_range": {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "confidence_level": "90%",
            "margin": margin
        },
        "features_used": {
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_3": lag_3,
            "rolling_avg_3": round(rolling_3, 2),
            "forecast_month": next_month_num
        },
        "limitation_notice": "Forecast based on historical seasonal trends; does not anticipate unannounced one-off expenses."
    }
