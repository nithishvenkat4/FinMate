"""Unit tests for deterministic financial calculations."""

from decimal import Decimal
import pytest
from app.services.calculations import (
    calculate_savings,
    calculate_savings_rate,
    calculate_goal_progress,
    calculate_percentage,
)


def test_calculate_savings_standard():
    income = Decimal("60000.00")
    expenses = Decimal("34450.00")
    savings = calculate_savings(income, expenses)
    assert savings == Decimal("25550.00")


def test_calculate_savings_negative():
    income = Decimal("30000.00")
    expenses = Decimal("45000.00")
    savings = calculate_savings(income, expenses)
    assert savings == Decimal("-15000.00")


def test_calculate_savings_rate_prompt_example():
    # Prompt section 13 example:
    # Income: 60,000 | Expenses: 34,450 | Savings: 25,550 -> 42.58%
    income = Decimal("60000.00")
    savings = Decimal("25550.00")
    rate = calculate_savings_rate(income, savings)
    assert rate == Decimal("42.58")


def test_calculate_savings_rate_zero_income():
    income = Decimal("0.00")
    savings = Decimal("5000.00")
    rate = calculate_savings_rate(income, savings)
    assert rate == Decimal("0.00")


def test_calculate_savings_rate_negative_savings():
    income = Decimal("50000.00")
    savings = Decimal("-10000.00")
    rate = calculate_savings_rate(income, savings)
    assert rate == Decimal("-20.00")


def test_calculate_goal_progress_partial():
    current = Decimal("65000.00")
    target = Decimal("100000.00")
    progress = calculate_goal_progress(current, target)
    assert progress == Decimal("65.00")


def test_calculate_goal_progress_zero_target():
    current = Decimal("5000.00")
    target = Decimal("0.00")
    progress = calculate_goal_progress(current, target)
    assert progress == Decimal("0.00")


def test_calculate_goal_progress_exceeded():
    current = Decimal("120000.00")
    target = Decimal("100000.00")
    progress = calculate_goal_progress(current, target)
    assert progress == Decimal("120.00")


def test_calculate_percentage_normal():
    part = Decimal("250.00")
    whole = Decimal("1000.00")
    pct = calculate_percentage(part, whole)
    assert pct == Decimal("25.00")
