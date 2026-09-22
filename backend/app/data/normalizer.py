"""Deterministic Data Normalization Layer for FinMate financial records."""

import datetime
from decimal import Decimal, InvalidOperation
import re
from typing import Optional, Tuple
from app.data.models import RawTransactionRow, NormalizedTransactionRow, QualityIssue, Severity


class DataNormalizer:
    TYPE_MAPPINGS = {
        "income": "income",
        "cr": "income",
        "credit": "income",
        "deposit": "income",
        "expense": "expense",
        "dr": "expense",
        "debit": "expense",
        "withdrawal": "expense",
        "payment": "expense",
    }

    DATE_FORMATS = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d.%m.%Y",
    ]

    @classmethod
    def normalize_description(cls, text: Optional[str]) -> str:
        if not text:
            return ""
        # Compact multi-whitespace into a single space
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def normalize_type(cls, raw_type: Optional[str]) -> Tuple[Optional[str], Optional[QualityIssue]]:
        if not raw_type:
            return None, QualityIssue(
                severity=Severity.ERROR,
                rule_code="MISSING_TYPE",
                message="Transaction type is missing.",
                field="type"
            )

        clean = raw_type.strip().lower()
        mapped = cls.TYPE_MAPPINGS.get(clean)
        if mapped:
            return mapped, None

        return None, QualityIssue(
            severity=Severity.ERROR,
            rule_code="INVALID_TYPE",
            message=f"Invalid transaction type '{raw_type}'. Expected 'income' or 'expense'.",
            field="type"
        )

    @classmethod
    def normalize_amount(cls, raw_amount: Optional[str]) -> Tuple[Optional[Decimal], Optional[QualityIssue]]:
        if not raw_amount:
            return None, QualityIssue(
                severity=Severity.ERROR,
                rule_code="MISSING_AMOUNT",
                message="Transaction amount is missing.",
                field="amount"
            )

        # Remove currency symbols (₹, $, €, £) and thousand separator commas
        cleaned = re.sub(r"[^\d.-]", "", raw_amount.strip())
        try:
            val = Decimal(cleaned)
            return val, None
        except (InvalidOperation, ValueError):
            return None, QualityIssue(
                severity=Severity.ERROR,
                rule_code="INVALID_AMOUNT_FORMAT",
                message=f"Amount '{raw_amount}' could not be parsed as an exact decimal number.",
                field="amount"
            )

    @classmethod
    def normalize_date(cls, raw_date: Optional[str]) -> Tuple[Optional[datetime.date], Optional[QualityIssue]]:
        if not raw_date:
            return None, QualityIssue(
                severity=Severity.ERROR,
                rule_code="MISSING_DATE",
                message="Transaction date is missing.",
                field="date"
            )

        clean = raw_date.strip()
        for fmt in cls.DATE_FORMATS:
            try:
                dt = datetime.datetime.strptime(clean, fmt).date()
                return dt, None
            except ValueError:
                continue

        return None, QualityIssue(
            severity=Severity.ERROR,
            rule_code="INVALID_DATE_FORMAT",
            message=f"Date '{raw_date}' is not in a recognized calendar format (e.g. YYYY-MM-DD or DD/MM/YYYY).",
            field="date"
        )

    @classmethod
    def normalize_category(cls, raw_cat: Optional[str], tx_type: Optional[str]) -> Tuple[str, Optional[QualityIssue]]:
        if not raw_cat or not raw_cat.strip():
            fallback = "Salary" if tx_type == "income" else "Other"
            return fallback, QualityIssue(
                severity=Severity.INFO,
                rule_code="CATEGORY_DEFAULTED",
                message=f"Category missing; defaulted to '{fallback}'.",
                field="category"
            )

        # Normalize title case and compact spaces
        clean = re.sub(r"\s+", " ", raw_cat.strip()).title()
        return clean, None

    @classmethod
    def normalize_row(cls, raw: RawTransactionRow) -> Tuple[Optional[NormalizedTransactionRow], list[QualityIssue]]:
        issues: list[QualityIssue] = []

        # Description
        desc = cls.normalize_description(raw.raw_description)
        if not desc:
            issues.append(QualityIssue(
                severity=Severity.ERROR,
                rule_code="EMPTY_DESCRIPTION",
                message="Transaction description must not be empty.",
                field="description"
            ))

        # Type
        t_type, type_issue = cls.normalize_type(raw.raw_type)
        if type_issue:
            issues.append(type_issue)

        # Amount
        amt, amt_issue = cls.normalize_amount(raw.raw_amount)
        if amt_issue:
            issues.append(amt_issue)

        # Date
        dt, date_issue = cls.normalize_date(raw.raw_date)
        if date_issue:
            issues.append(date_issue)

        # Category
        cat, cat_issue = cls.normalize_category(raw.raw_category, t_type)
        if cat_issue:
            issues.append(cat_issue)

        # Notes
        notes = cls.normalize_description(raw.raw_notes) or None

        # Check if there are blocking ERROR severity issues
        has_errors = any(i.severity == Severity.ERROR for i in issues)
        if has_errors or not dt or amt is None or not t_type or not desc:
            return None, issues

        normalized = NormalizedTransactionRow(
            transaction_date=dt,
            description=desc,
            amount=amt,
            transaction_type=t_type,
            category=cat,
            notes=notes
        )
        return normalized, issues
