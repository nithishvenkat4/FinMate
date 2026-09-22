# FinMate Data Ingestion Pipeline

## Architecture Overview

FinMate implements a multi-stage data ingestion pipeline separating file parsing, schema normalization, rule-based quality evaluation, and database persistence.

```
Upload CSV
    ↓
File Security & Boundary Checks (<5MB, CSV Extension)
    ↓
Encoding Detection (UTF-8, UTF-8-SIG, Latin-1)
    ↓
Header Mapping & Delimiter Detection
    ↓
Row-by-Row Parser (app/data/parser.py)
    ↓
Deterministic Normalizer (app/data/normalizer.py)
    ↓
Data Quality Engine (app/data/rules.py - 11 Rules)
    ↓
Deduplication Heuristic & Severity Triage
    ↓
┌─────────────────────────────────┴─────────────────────────────────┐
│ Preview Mode (POST /preview)       Persistence Mode (POST /transactions) │
│ Returns validation summary only     Stores ImportRecord & Transactions     │
└─────────────────────────────────┬─────────────────────────────────┘
                                  ↓
                       PostgreSQL / Database
```

## Security & Boundary Safeguards
1. **File Size Limit**: Strictly enforced at 5 MB max to prevent memory exhaustion (DoS).
2. **File Type Verification**: Validates file extension (`.csv`) and MIME type (`text/csv`).
3. **Safe Storage**: Uploaded files are streamed in memory without filesystem execution.
4. **No Arbitrary Code Execution**: CSV cell values are parsed into typed models without script evaluation.
