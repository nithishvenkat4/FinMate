# Model Card: Monthly Expense Forecaster

## 1. Model Details
- **Model Name**: `RidgeRegressionForecaster`
- **Version**: `v1.0`
- **Task**: Time-Series Monthly Expense Regression
- **Algorithm**: Ridge Regression (`Ridge(alpha=1.0)`) with L2 regularization
- **Features**: Strictly historical lagged features (`lag_1`, `lag_2`, `lag_3`, `rolling_avg_3`, `month_num`).
- **Owner / Module**: `app.ai.models.forecaster`

## 2. Intended Use
- **Primary Intended Use**: Provide an estimated baseline of upcoming aggregate monthly expenses to assist cashflow and savings planning.
- **Non-Intended Use**: Guaranteeing exact outlays, predicting stock market returns, or replacing detailed household budgeting.

## 3. Training & Evaluation Data
- **Training Dataset**: `data/training/expenses_monthly_train.csv` (33 months of chronological spending series: 2022-04 to 2024-12).
- **Evaluation Dataset**: `data/evaluation/expenses_monthly_eval.csv` (12 held-out future months: 2025-01 to 2025-12).

## 4. Measured Performance
- **TimeSeriesSplit CV MAE**: ₹3,905.17
- **Future Holdout MAE**: ₹3,369.93
- **Future Holdout RMSE**: ₹3,620.15
- **Future Holdout $R^2$**: 0.1872
- **Residual Standard Deviation**: ₹1,842.10

## 5. Decision Safeguards & Limitations
- **No False Precision**: Forecast point estimates are rounded to the nearest ₹50.
- **Uncertainty Interval**: Explicit 90% confidence range ($\pm 1.645\sigma$) is always displayed alongside the point prediction.
- **Limitation**: The model captures recurrent seasonal patterns but cannot predict one-off major emergencies or medical events.
