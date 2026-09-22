# FinMate Data Lineage & Auditability

## Overview
Every transaction in FinMate tracks provenance metadata to ensure data lineage and auditable traceability.

## Lineage Attributes

Each `transactions` row records:
- `source_type`: Origin mechanism (`manual`, `csv_import`, `synthetic`).
- `source_reference`: Reference identifier (e.g. original uploaded filename `september_txns.csv`).
- `import_id`: UUID foreign key linking to the `import_records` batch audit log.
- `data_quality_flags`: JSON array string of active quality warning codes attached during ingestion (e.g. `["POSSIBLE_DUPLICATE_IN_DB", "FUTURE_TRANSACTION_DATE"]`).

## Batch Audit Table (`import_records`)
Maintains an immutable record of every CSV file uploaded:
- `id`: UUID
- `user_id`: Owning user
- `filename`: Uploaded file name
- `source_type`: `csv_import`
- `total_rows`: Total records parsed
- `accepted_rows`: Count of clean records persisted
- `rejected_rows`: Count of malformed records rejected
- `warning_rows`: Count of rows with review warnings
- `duplicate_rows`: Count of duplicate candidates detected
- `status`: `completed`, `completed_with_warnings`, or `failed`
- `created_at`: Timestamp of import execution
