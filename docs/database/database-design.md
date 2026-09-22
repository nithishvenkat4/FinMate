# FinMate Database Architecture & Entity-Relationship Model

## ER Diagram (Phase 2)

```mermaid
erDiagram
    USERS ||--o| FINANCIAL_PROFILES : owns
    USERS ||--o{ TRANSACTIONS : records
    USERS ||--o{ GOALS : plans
    USERS ||--o{ INVESTMENTS : holds
    USERS ||--o{ FEEDBACKS : provides
    USERS ||--o{ IMPORT_RECORDS : uploads
    TRANSACTION_CATEGORIES ||--o{ TRANSACTIONS : categorizes
    IMPORT_RECORDS ||--o{ TRANSACTIONS : originates

    USERS {
        uuid id PK
        string name
        string email UK
        datetime created_at
        datetime updated_at
    }

    FINANCIAL_PROFILES {
        uuid id PK
        uuid user_id FK,UK
        numeric monthly_income
        numeric monthly_fixed_expenses
        numeric current_savings
        string risk_preference
        datetime created_at
        datetime updated_at
    }

    TRANSACTION_CATEGORIES {
        uuid id PK
        string name UK
        string category_type
        string description
        boolean is_active
        datetime created_at
    }

    IMPORT_RECORDS {
        uuid id PK
        uuid user_id FK
        string filename
        string source_type
        integer total_rows
        integer accepted_rows
        integer rejected_rows
        integer warning_rows
        integer duplicate_rows
        string status
        text error_summary
        datetime created_at
    }

    TRANSACTIONS {
        uuid id PK
        uuid user_id FK
        uuid category_id FK
        uuid import_id FK
        date transaction_date
        string description
        numeric amount
        string transaction_type
        string category
        text notes
        string source_type
        string source_reference
        text data_quality_flags
        datetime created_at
        datetime updated_at
    }

    GOALS {
        uuid id PK
        uuid user_id FK
        string name
        numeric target_amount
        numeric current_amount
        date target_date
        string priority
        datetime created_at
        datetime updated_at
    }

    INVESTMENTS {
        uuid id PK
        uuid user_id FK
        string asset_name
        string investment_type
        numeric quantity
        numeric current_value
        datetime created_at
        datetime updated_at
    }
```

## Critical Constraints
- `amount > 0`: Enforced by database check constraint `ck_transactions_amount_positive`.
- Primary keys: UUIDs throughout all entities.
- Monies: `NUMERIC(15, 2)` (no floating point imprecision).
- Lineage: Foreign key links from `transactions.import_id` to `import_records.id`.
