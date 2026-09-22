"""Unit tests for Data Quality Rules Engine."""

import datetime
from decimal import Decimal
import uuid
from app.data.models import NormalizedTransactionRow, Severity
from app.data.rules import DataQualityEngine


def test_rule_1_non_positive_amount():
    row = NormalizedTransactionRow(
        transaction_date=datetime.date(2026, 9, 1),
        description="Zero test",
        amount=Decimal("0.00"),
        transaction_type="expense",
        category="Food"
    )
    is_valid, is_dup, issues = DataQualityEngine.evaluate_row(row, user_id=uuid.uuid4())
    assert not is_valid
    assert any(i.severity == Severity.ERROR and i.rule_code == "NON_POSITIVE_AMOUNT" for i in issues)


def test_rule_7_category_mismatch_warning():
    row = NormalizedTransactionRow(
        transaction_date=datetime.date(2026, 9, 1),
        description="Misclassified Salary",
        amount=Decimal("50000.00"),
        transaction_type="expense",
        category="Salary"
    )
    is_valid, is_dup, issues = DataQualityEngine.evaluate_row(row, user_id=uuid.uuid4())
    assert is_valid  # Still valid to enter clean dataset, but produces warning
    assert any(i.severity == Severity.WARNING and i.rule_code == "CATEGORY_TYPE_MISMATCH" for i in issues)


def test_rule_9_large_transaction_warning():
    row = NormalizedTransactionRow(
        transaction_date=datetime.date(2026, 9, 1),
        description="Property Purchase",
        amount=Decimal("1500000.00"),  # ₹15 Lakhs
        transaction_type="expense",
        category="Other"
    )
    is_valid, is_dup, issues = DataQualityEngine.evaluate_row(row, user_id=uuid.uuid4())
    assert is_valid
    assert any(i.severity == Severity.WARNING and i.rule_code == "LARGE_TRANSACTION_AMOUNT" for i in issues)


def test_rule_10_future_transaction_warning():
    future_date = datetime.date.today() + datetime.timedelta(days=30)
    row = NormalizedTransactionRow(
        transaction_date=future_date,
        description="Advance Booking",
        amount=Decimal("5000.00"),
        transaction_type="expense",
        category="Transport"
    )
    is_valid, is_dup, issues = DataQualityEngine.evaluate_row(row, user_id=uuid.uuid4())
    assert is_valid
    assert any(i.severity == Severity.WARNING and i.rule_code == "FUTURE_TRANSACTION_DATE" for i in issues)


def test_rule_11_duplicate_in_batch():
    user_id = uuid.uuid4()
    seen_keys = set()

    row1 = NormalizedTransactionRow(
        transaction_date=datetime.date(2026, 9, 1),
        description="Swiggy Order",
        amount=Decimal("450.00"),
        transaction_type="expense",
        category="Food"
    )
    is_valid1, is_dup1, issues1 = DataQualityEngine.evaluate_row(row1, user_id=user_id, seen_batch_keys=seen_keys)
    assert not is_dup1

    # Second row with identical date, amount, description
    row2 = NormalizedTransactionRow(
        transaction_date=datetime.date(2026, 9, 1),
        description="Swiggy Order",
        amount=Decimal("450.00"),
        transaction_type="expense",
        category="Food"
    )
    is_valid2, is_dup2, issues2 = DataQualityEngine.evaluate_row(row2, user_id=user_id, seen_batch_keys=seen_keys)
    assert is_dup2
    assert any(i.severity == Severity.WARNING and i.rule_code == "POSSIBLE_DUPLICATE_IN_BATCH" for i in issues2)
