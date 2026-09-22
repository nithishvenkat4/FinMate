"""Unit tests for Pydantic schema validations."""

from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.transaction import TransactionCreate
from app.schemas.goal import GoalCreate
from app.schemas.user import UserCreate


def test_transaction_schema_valid():
    tx = TransactionCreate(
        description="Grocery shopping",
        amount=Decimal("1500.50"),
        transaction_type="expense",
        category="Food"
    )
    assert tx.amount == Decimal("1500.50")
    assert tx.transaction_type == "expense"


def test_transaction_schema_negative_amount_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(
            description="Invalid transaction",
            amount=Decimal("-500.00"),
            transaction_type="expense",
            category="Food"
        )


def test_goal_schema_zero_target_rejected():
    with pytest.raises(ValidationError):
        GoalCreate(
            name="New Laptop",
            target_amount=Decimal("0.00"),
            target_date="2026-12-31"
        )


def test_user_schema_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            name="Aarav Sharma",
            email="not-an-email"
        )
