"""Data Quality Rules Engine implementing Rules 1 through 11."""

import datetime
from decimal import Decimal
from typing import List, Optional, Set, Tuple
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.data.models import NormalizedTransactionRow, QualityIssue, Severity
from app.models.transaction import Transaction

LARGE_TRANSACTION_THRESHOLD = Decimal("1000000.00")  # ₹10,00,000 (10 Lakhs)

INCOME_TYPICAL_CATEGORIES = {"Salary", "Freelance", "Investment", "Other Income", "Dividend", "Interest"}
EXPENSE_TYPICAL_CATEGORIES = {"Food", "Shopping", "Transport", "Utilities", "Rent", "Healthcare", "Education", "Entertainment", "Other"}


class DataQualityEngine:
    @classmethod
    def evaluate_row(
        cls,
        row: NormalizedTransactionRow,
        user_id: uuid.UUID,
        db: Optional[Session] = None,
        seen_batch_keys: Optional[Set[Tuple[datetime.date, Decimal, str]]] = None,
    ) -> Tuple[bool, bool, List[QualityIssue]]:
        """Evaluates a normalized transaction against Data Quality rules.

        Returns:
            (is_valid, is_duplicate_candidate, list_of_issues)
        """
        issues: List[QualityIssue] = []
        is_duplicate = False

        # RULE 1: Amount must be greater than zero
        if row.amount <= Decimal("0.00"):
            issues.append(QualityIssue(
                severity=Severity.ERROR,
                rule_code="NON_POSITIVE_AMOUNT",
                message=f"Transaction amount ({row.amount}) must be strictly greater than zero.",
                field="amount"
            ))

        # RULE 2: Transaction type must be income or expense
        if row.transaction_type not in ("income", "expense"):
            issues.append(QualityIssue(
                severity=Severity.ERROR,
                rule_code="INVALID_TYPE",
                message=f"Invalid transaction type '{row.transaction_type}'.",
                field="type"
            ))

        # RULE 4: Description must not be empty
        if not row.description.strip():
            issues.append(QualityIssue(
                severity=Severity.ERROR,
                rule_code="EMPTY_DESCRIPTION",
                message="Transaction description must not be empty.",
                field="description"
            ))

        # RULE 7: Category compatibility warning
        if row.transaction_type == "expense" and row.category in INCOME_TYPICAL_CATEGORIES:
            issues.append(QualityIssue(
                severity=Severity.WARNING,
                rule_code="CATEGORY_TYPE_MISMATCH",
                message=f"Category '{row.category}' is typically an income category, but transaction is marked as 'expense'.",
                field="category"
            ))
        elif row.transaction_type == "income" and row.category in EXPENSE_TYPICAL_CATEGORIES - {"Other"}:
            issues.append(QualityIssue(
                severity=Severity.WARNING,
                rule_code="CATEGORY_TYPE_MISMATCH",
                message=f"Category '{row.category}' is typically an expense category, but transaction is marked as 'income'.",
                field="category"
            ))

        # RULE 9: Extremely large transactions warning
        if row.amount >= LARGE_TRANSACTION_THRESHOLD:
            issues.append(QualityIssue(
                severity=Severity.WARNING,
                rule_code="LARGE_TRANSACTION_AMOUNT",
                message=f"Amount ₹{row.amount:,.2f} exceeds high-value threshold (₹10,00,000). Please review for entry accuracy.",
                field="amount"
            ))

        # RULE 10: Future transaction date warning
        today = datetime.date.today()
        if row.transaction_date > today:
            issues.append(QualityIssue(
                severity=Severity.WARNING,
                rule_code="FUTURE_TRANSACTION_DATE",
                message=f"Transaction date {row.transaction_date} is in the future (today is {today}).",
                field="date"
            ))

        # RULE 11: Potential Duplicate Detection Heuristic
        # Key: (date, amount, description)
        dedup_key = (row.transaction_date, row.amount, row.description.lower())

        # Check within current import batch
        if seen_batch_keys is not None:
            if dedup_key in seen_batch_keys:
                is_duplicate = True
                issues.append(QualityIssue(
                    severity=Severity.WARNING,
                    rule_code="POSSIBLE_DUPLICATE_IN_BATCH",
                    message="Matches another row with the same date, amount, and description within this file.",
                    field="description"
                ))
            else:
                seen_batch_keys.add(dedup_key)

        # Check against existing transactions in the database for this user
        if db is not None and not is_duplicate:
            stmt = (
                select(Transaction.id)
                .where(
                    Transaction.user_id == user_id,
                    Transaction.transaction_date == row.transaction_date,
                    Transaction.amount == row.amount,
                    Transaction.description == row.description
                )
                .limit(1)
            )
            existing_match = db.scalars(stmt).first()
            if existing_match:
                is_duplicate = True
                issues.append(QualityIssue(
                    severity=Severity.WARNING,
                    rule_code="POSSIBLE_DUPLICATE_IN_DB",
                    message="Matches an existing transaction already recorded in your account (same date, amount, description).",
                    field="description"
                ))

        has_blocking_errors = any(i.severity == Severity.ERROR for i in issues)
        is_valid = not has_blocking_errors

        return is_valid, is_duplicate, issues
