# FinMate API Specification

## Base URL
`/api/v1`

## Endpoints Summary

### Health
- `GET /health`: Service health check and database connectivity status.

### Data Ingestion & Imports (Phase 2)
- `POST /api/v1/imports/transactions`: Multipart upload for CSV ingestion and persistence.
- `POST /api/v1/imports/transactions/preview`: Non-persisting CSV preview with row-level validation.
- `GET /api/v1/imports/history`: Returns batch import audit records.

### Data Quality (Phase 2)
- `GET /api/v1/data-quality/summary`: Aggregate metrics on clean, warning, duplicate, and future-dated transactions.

### Categories (Phase 2)
- `GET /api/v1/categories`: Lists active transaction categories.
- `POST /api/v1/categories`: Creates a new custom category.
- `PUT /api/v1/categories/{id}`: Modifies category name or toggles `is_active` (soft deactivation).

### Transactions
- `GET /api/v1/transactions`: Paginated transaction ledger with filters (`transaction_type`, `category`, `page`, `page_size`).
- `POST /api/v1/transactions`: Creates a single transaction with manual lineage.
- `GET /api/v1/transactions/{id}`: Retrieves transaction by UUID.
- `PUT /api/v1/transactions/{id}`: Updates transaction fields.
- `DELETE /api/v1/transactions/{id}`: Removes transaction record.

### Goals
- `GET /api/v1/goals`: Lists user goals with calculated `progress_percentage`.
- `POST /api/v1/goals`: Creates new financial goal.
- `GET /api/v1/goals/{id}`: Retrieves goal.
- `PUT /api/v1/goals/{id}`: Updates goal amount or dates.
- `DELETE /api/v1/goals/{id}`: Deletes goal.

### Investments
- `GET /api/v1/investments`: Lists portfolio assets.
- `POST /api/v1/investments`: Records investment holding.
- `PUT /api/v1/investments/{id}`: Updates asset value or quantity.
- `DELETE /api/v1/investments/{id}`: Removes investment record.

### Financial Profile
- `GET /api/v1/profile`: Retrieves profile baselines.
- `PUT /api/v1/profile`: Updates income, fixed expenses, current savings, and risk preference.

### Analytics
- `GET /api/v1/analytics/summary`: Deterministic financial summary (income, expenses, net cash flow, savings rate, category breakdown).
