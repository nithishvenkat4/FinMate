"""Unit tests for Monthly Expense Forecasting models and time-aware evaluation."""

import numpy as np
import pytest
from app.ai.models.forecaster import (
    MovingAverageBaselineForecaster,
    build_ridge_forecaster,
    evaluate_forecaster_time_series,
    forecast_next_period
)


def test_moving_average_baseline():
    baseline = MovingAverageBaselineForecaster()
    # Feature matrix with rolling_avg_3 in column index 3
    X = np.array([
        [30000.0, 31000.0, 32000.0, 31000.0, 4.0],
        [31000.0, 32000.0, 33000.0, 32000.0, 5.0],
    ])
    preds = baseline.predict(X)
    assert np.allclose(preds, [31000.0, 32000.0])


def test_time_series_cv_evaluation():
    model = build_ridge_forecaster()
    # 8 consecutive months
    X = np.array([
        [28000.0, 29000.0, 30000.0, 29000.0, 1.0],
        [29000.0, 30000.0, 31000.0, 30000.0, 2.0],
        [30000.0, 31000.0, 32000.0, 31000.0, 3.0],
        [31000.0, 32000.0, 33000.0, 32000.0, 4.0],
        [32000.0, 33000.0, 34000.0, 33000.0, 5.0],
        [33000.0, 34000.0, 35000.0, 34000.0, 6.0],
    ])
    y = np.array([31500.0, 32200.0, 33100.0, 34000.0, 35200.0, 36100.0])

    res = evaluate_forecaster_time_series(model, X, y, n_splits=2)
    assert "cv_mae" in res
    assert "cv_rmse" in res
    assert res["cv_mae"] > 0


def test_forecast_next_period_with_uncertainty():
    model = build_ridge_forecaster()
    X = np.array([
        [30000.0, 31000.0, 32000.0, 31000.0, 4.0],
        [31000.0, 32000.0, 33000.0, 32000.0, 5.0],
    ])
    y = np.array([32500.0, 33500.0])
    model.fit(X, y)

    res = forecast_next_period(model, recent_lags=[33500.0, 32000.0, 31000.0], next_month_num=6, residual_std=1500.0)
    assert res["predicted_expense"] is not None
    assert "uncertainty_range" in res
    assert res["uncertainty_range"]["lower_bound"] < res["predicted_expense"]
    assert res["uncertainty_range"]["upper_bound"] > res["predicted_expense"]
    assert res["uncertainty_range"]["confidence_level"] == "90%"


def test_forecast_insufficient_lags():
    model = build_ridge_forecaster()
    res = forecast_next_period(model, recent_lags=[33000.0], next_month_num=6)
    assert res["predicted_expense"] is None
    assert "error" in res
