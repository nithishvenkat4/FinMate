"""Deterministic financial calculations engine.

CRITICAL ARCHITECTURAL RULE:
All mathematical calculations (savings, savings rate, goal progress, category percentages)
MUST be computed here deterministically using Python's Decimal library for exact precision.
The LLM must NEVER be the authoritative calculator.
"""

from decimal import Decimal, ROUND_HALF_UP

TWO_PLACES = Decimal("0.01")


def to_decimal(val: object) -> Decimal:
    """Safely converts numerical or string inputs to Decimal."""
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.00")


def calculate_savings(income: Decimal, expenses: Decimal) -> Decimal:
    """Calculates net savings = income - expenses.

    Args:
        income: Total incoming funds
        expenses: Total outgoing funds

    Returns:
        Decimal representation of net savings rounded to 2 places.
    """
    inc = to_decimal(income)
    exp = to_decimal(expenses)
    result = inc - exp
    return result.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_savings_rate(income: Decimal, savings: Decimal) -> Decimal:
    """Calculates savings rate percentage: (savings / income) * 100.

    Rules:
    - If income <= 0, savings rate is 0.00% (or 0.00 when savings <= 0).
    - Precision is rounded to 2 decimal places.

    Args:
        income: Total incoming funds
        savings: Net savings

    Returns:
        Savings rate as a percentage Decimal (e.g., Decimal("42.58")).
    """
    inc = to_decimal(income)
    sav = to_decimal(savings)

    if inc <= Decimal("0.00"):
        return Decimal("0.00")

    rate = (sav / inc) * Decimal("100.00")
    return rate.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_goal_progress(current_amount: Decimal, target_amount: Decimal) -> Decimal:
    """Calculates progress towards a financial target: (current / target) * 100.

    Args:
        current_amount: Amount saved so far
        target_amount: Target goal amount

    Returns:
        Progress as a percentage Decimal (e.g., Decimal("65.50")).
        Returns 0.00 if target_amount <= 0.
    """
    current = to_decimal(current_amount)
    target = to_decimal(target_amount)

    if target <= Decimal("0.00"):
        return Decimal("0.00")

    if current < Decimal("0.00"):
        return Decimal("0.00")

    progress = (current / target) * Decimal("100.00")
    return progress.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_percentage(part: Decimal, whole: Decimal) -> Decimal:
    """Calculates portion percentage: (part / whole) * 100."""
    p = to_decimal(part)
    w = to_decimal(whole)

    if w <= Decimal("0.00"):
        return Decimal("0.00")

    pct = (p / w) * Decimal("100.00")
    return pct.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
