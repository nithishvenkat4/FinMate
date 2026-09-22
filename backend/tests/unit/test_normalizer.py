"""Unit tests for Data Normalizer."""

import datetime
from decimal import Decimal
from app.data.models import RawTransactionRow, Severity
from app.data.normalizer import DataNormalizer


def test_normalize_valid_row():
    raw = RawTransactionRow(
        row_number=2,
        raw_date="  2026-09-02 ",
        raw_description="   Swiggy   Dinner  ",
        raw_amount="  ₹ 450.50 ",
        raw_type="  EXPENSE  ",
        raw_category=" food ",
        raw_notes=" Late night snack "
    )
    norm, issues = DataNormalizer.normalize_row(raw)
    assert norm is not None
    assert norm.transaction_date == datetime.date(2026, 9, 2)
    assert norm.description == "Swiggy Dinner"
    assert norm.amount == Decimal("450.50")
    assert norm.transaction_type == "expense"
    assert norm.category == "Food"
    assert norm.notes == "Late night snack"


def test_normalize_alternate_date_formats():
    raw = RawTransactionRow(
        row_number=2,
        raw_date="05/09/2026",
        raw_description="Netflix",
        raw_amount="649.00",
        raw_type="expense",
        raw_category="Entertainment"
    )
    norm, issues = DataNormalizer.normalize_row(raw)
    assert norm is not None
    assert norm.transaction_date == datetime.date(2026, 9, 5)


def test_normalize_invalid_amount_produces_error():
    raw = RawTransactionRow(
        row_number=3,
        raw_date="2026-09-02",
        raw_description="Invalid",
        raw_amount="abc_invalid",
        raw_type="expense"
    )
    norm, issues = DataNormalizer.normalize_row(raw)
    assert norm is None
    assert any(i.severity == Severity.ERROR and i.rule_code == "INVALID_AMOUNT_FORMAT" for i in issues)


def test_normalize_invalid_type_produces_error():
    raw = RawTransactionRow(
        row_number=4,
        raw_date="2026-09-02",
        raw_description="Invalid Type",
        raw_amount="500",
        raw_type="unknown_type"
    )
    norm, issues = DataNormalizer.normalize_row(raw)
    assert norm is None
    assert any(i.severity == Severity.ERROR and i.rule_code == "INVALID_TYPE" for i in issues)


def test_normalize_missing_category_defaults_with_info():
    raw = RawTransactionRow(
        row_number=5,
        raw_date="2026-09-01",
        raw_description="Salary Payment",
        raw_amount="60000",
        raw_type="income",
        raw_category=""
    )
    norm, issues = DataNormalizer.normalize_row(raw)
    assert norm is not None
    assert norm.category == "Salary"
    assert any(i.severity == Severity.INFO and i.rule_code == "CATEGORY_DEFAULTED" for i in issues)
