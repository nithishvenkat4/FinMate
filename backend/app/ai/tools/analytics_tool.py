"""Agent tool interface exposing deterministic domain services."""

from decimal import Decimal
from app.services.calculations import calculate_savings, calculate_savings_rate, calculate_goal_progress


class DeterministicFinancialTool:
    """Tool exposed to future agents to perform verified mathematical operations."""

    @staticmethod
    def compute_savings(income: Decimal, expenses: Decimal) -> Decimal:
        return calculate_savings(income, expenses)

    @staticmethod
    def compute_savings_rate(income: Decimal, savings: Decimal) -> Decimal:
        return calculate_savings_rate(income, savings)

    @staticmethod
    def compute_goal_progress(current: Decimal, target: Decimal) -> Decimal:
        return calculate_goal_progress(current, target)
