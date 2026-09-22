"""Data Ingestion & Quality Pipeline orchestrator."""

import json
from typing import Optional, Set, Tuple
import uuid
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.data.models import (
    ImportSummaryResult,
    NormalizedTransactionRow,
    QualityIssue,
    RowValidationResult,
    Severity,
)
from app.data.normalizer import DataNormalizer
from app.data.parser import CSVParser, CSVParseException
from app.data.rules import DataQualityEngine
from app.models.import_record import ImportRecord
from app.models.transaction import Transaction
from app.repositories.category_repo import CategoryRepository


class IngestionPipeline:
    @classmethod
    def process_csv(
        cls,
        user_id: uuid.UUID,
        content: str,
        filename: str,
        db: Optional[Session] = None,
        persist: bool = False,
    ) -> ImportSummaryResult:
        """Processes a CSV file through parsing, normalization, quality evaluation, and persistence."""
        import_id = uuid.uuid4()
        logger.info("Starting CSV ingestion pipeline for user %s (file: %s, persist: %s, import_id: %s)",
                    user_id, filename, persist, import_id)

        try:
            raw_rows, parse_errors = CSVParser.parse(content)
        except CSVParseException as exc:
            logger.warning("CSV parse error for user %s: %s", user_id, exc.message)
            return ImportSummaryResult(
                import_id=import_id,
                filename=filename,
                total_rows=0,
                status="failed",
                errors=[exc.message]
            )

        row_results: list[RowValidationResult] = []
        valid_rows_count = 0
        invalid_rows_count = 0
        warning_rows_count = 0
        duplicate_rows_count = 0

        seen_batch_keys: Set[Tuple] = set()
        transactions_to_persist: list[Tuple[NormalizedTransactionRow, list[QualityIssue]]] = []

        for raw_row in raw_rows:
            raw_dict = {
                "date": raw_row.raw_date,
                "description": raw_row.raw_description,
                "amount": raw_row.raw_amount,
                "type": raw_row.raw_type,
                "category": raw_row.raw_category,
                "notes": raw_row.raw_notes,
            }

            # 1. Normalization
            normalized, norm_issues = DataNormalizer.normalize_row(raw_row)

            if not normalized:
                invalid_rows_count += 1
                row_results.append(RowValidationResult(
                    row_number=raw_row.row_number,
                    raw_data=raw_dict,
                    normalized_data=None,
                    is_valid=False,
                    is_duplicate_candidate=False,
                    issues=norm_issues
                ))
                continue

            # 2. Quality Rules & Duplicate Evaluation
            is_valid, is_dup, qual_issues = DataQualityEngine.evaluate_row(
                row=normalized,
                user_id=user_id,
                db=db,
                seen_batch_keys=seen_batch_keys
            )

            all_issues = norm_issues + qual_issues
            has_warnings = any(i.severity == Severity.WARNING for i in all_issues)
            has_errors = any(i.severity == Severity.ERROR for i in all_issues)

            if has_warnings:
                warning_rows_count += 1
            if is_dup:
                duplicate_rows_count += 1

            if is_valid and not has_errors:
                valid_rows_count += 1
                transactions_to_persist.append((normalized, all_issues))
            else:
                invalid_rows_count += 1

            row_results.append(RowValidationResult(
                row_number=raw_row.row_number,
                raw_data=raw_dict,
                normalized_data=normalized,
                is_valid=is_valid and not has_errors,
                is_duplicate_candidate=is_dup,
                issues=all_issues
            ))

        # Determine Overall Status
        total_rows = len(raw_rows)
        if invalid_rows_count == total_rows and total_rows > 0:
            status = "failed"
        elif warning_rows_count > 0 or invalid_rows_count > 0:
            status = "completed_with_warnings"
        else:
            status = "completed"

        # Persistence
        if persist and db is not None and valid_rows_count > 0:
            category_repo = CategoryRepository(db)
            category_repo.seed_defaults()

            # Record audit batch
            record = ImportRecord(
                id=import_id,
                user_id=user_id,
                filename=filename,
                source_type="csv_import",
                total_rows=total_rows,
                accepted_rows=valid_rows_count,
                rejected_rows=invalid_rows_count,
                warning_rows=warning_rows_count,
                duplicate_rows=duplicate_rows_count,
                status=status
            )
            db.add(record)

            # Persist transactions
            for norm_tx, issues in transactions_to_persist:
                cat = category_repo.get_or_create(norm_tx.category, norm_tx.transaction_type)
                warning_codes = [i.rule_code for i in issues if i.severity == Severity.WARNING]

                tx_entity = Transaction(
                    user_id=user_id,
                    category_id=cat.id,
                    transaction_date=norm_tx.transaction_date,
                    description=norm_tx.description,
                    amount=norm_tx.amount,
                    transaction_type=norm_tx.transaction_type,
                    category=cat.name,
                    notes=norm_tx.notes,
                    source_type="csv_import",
                    source_reference=filename,
                    import_id=import_id,
                    data_quality_flags=json.dumps(warning_codes) if warning_codes else None
                )
                db.add(tx_entity)

            db.commit()
            logger.info("Successfully persisted %d transactions for user %s (import_id: %s)",
                        valid_rows_count, user_id, import_id)

        return ImportSummaryResult(
            import_id=import_id,
            filename=filename,
            source_type="csv_import",
            total_rows=total_rows,
            valid_rows=valid_rows_count,
            invalid_rows=invalid_rows_count,
            warning_rows=warning_rows_count,
            duplicate_rows=duplicate_rows_count,
            status=status,
            errors=parse_errors,
            row_results=row_results
        )
