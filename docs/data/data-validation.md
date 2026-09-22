# FinMate Data Validation Specification

## Multi-Tier Validation Strategy

Validation in FinMate operates across three protective layers:

1. **Frontend Layer**: Immediate user feedback preventing obviously invalid form submissions.
2. **API & Pydantic Layer**: Request body schema validation, positive amount checking, and email validation.
3. **Database Layer**: Hard `CheckConstraint` invariants (`amount > 0`, `monthly_income >= 0`) and foreign-key integrity.

## Normalization & Parsing Rules

### Monetary Values
- Stored as `NUMERIC(15, 2)`.
- Handled in Python exclusively with `decimal.Decimal` with `ROUND_HALF_UP` rounding.
- Floats are strictly prohibited for authoritative monetary calculations.

### Transaction Types
- Canonical values: `income` and `expense`.
- Mapped aliases:
  - `income`: `cr`, `credit`, `deposit`
  - `expense`: `dr`, `debit`, `withdrawal`, `payment`

### Calendar Dates
- Supported formats:
  - `YYYY-MM-DD` (ISO 8601)
  - `DD-MM-YYYY`
  - `DD/MM/YYYY`
  - `YYYY/MM/DD`
- Handled as `datetime.date` objects.
