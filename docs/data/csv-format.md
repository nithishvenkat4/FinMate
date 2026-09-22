# FinMate CSV Ingestion Format Specification

## Overview
FinMate Phase 2 implements a robust CSV transaction ingestion engine that parses, normalizes, and validates financial transaction records.

## Expected Schema

| Column Name | Required / Optional | Data Type | Permitted Formats / Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `date` | **Required** | Date | `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY` | Calendar date of transaction execution. Future dates trigger warning. |
| `description` | **Required** | String | Non-empty text, max 255 chars | Payee or transaction memo (e.g. Swiggy, Salary). |
| `amount` | **Required** | Numeric | Exact Decimal &gt; 0.00 | Transaction amount. Must be strictly positive. |
| `type` | **Required** | Enum | `income` or `expense` (or `cr`/`dr`, `credit`/`debit`) | Direction of fund movement. |
| `category` | Optional | String | Valid category name (e.g. Food, Shopping) | If omitted, defaults to `Salary` for income or `Other` for expense. |
| `notes` | Optional | String | Text | Optional user remarks or invoice memo. |

## Canonical Example

```csv
date,description,amount,type,category,notes
2026-09-01,Salary,60000,income,Salary,Monthly salary
2026-09-02,Swiggy,450,expense,Food,Dinner
2026-09-03,Amazon,1200,expense,Shopping,Electronics
2026-09-04,Uber,300,expense,Transport,Cab
2026-09-05,Netflix,649,expense,Entertainment,Subscription
2026-09-06,Electricity,1800,expense,Utilities,Power bill
```

## Fault Tolerance & Normalization Rules
1. **Delimiter Handling**: Detects both comma (`,`) and semicolon (`;`) delimiters.
2. **Encodings**: Supports UTF-8, UTF-8-SIG (BOM removal), and Latin-1.
3. **Extra Columns**: Ignored without failing the import.
4. **Currency Symbols**: Automatic stripping of `₹`, `$`, `€`, and `,` separators.
5. **Whitespace**: Automatic trimming of leading/trailing spaces and compression of internal spaces.
