"""Analytics request and response schemas."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class CategorySpendingItem(BaseModel):
    category: str
    total_amount: Decimal
    percentage: Decimal
    transaction_count: int


class MonthlyCashFlowItem(BaseModel):
    month: str  # e.g. "2026-03"
    income: Decimal
    expense: Decimal
    net_savings: Decimal


class AnalyticsSummaryResponse(BaseModel):
    total_income: Decimal = Field(default=Decimal("0.00"), description="Sum of all recorded income transactions")
    total_expenses: Decimal = Field(default=Decimal("0.00"), description="Sum of all recorded expense transactions")
    net_savings: Decimal = Field(default=Decimal("0.00"), description="Total Income - Total Expenses")
    savings_rate: Decimal = Field(default=Decimal("0.00"), description="Percentage of income saved: (net_savings / total_income) * 100")
    transaction_count: int = Field(default=0, description="Total count of transactions recorded")

    # Profile baselines
    profile_monthly_income: Optional[Decimal] = Decimal("0.00")
    profile_monthly_fixed_expenses: Optional[Decimal] = Decimal("0.00")
    profile_current_savings: Optional[Decimal] = Decimal("0.00")

    # Goals and Investments overview
    active_goals_count: int = 0
    total_investments_value: Decimal = Decimal("0.00")

    # Category breakdowns for charts
    category_breakdown: List[CategorySpendingItem] = Field(default_factory=list)
    recent_cash_flow: List[MonthlyCashFlowItem] = Field(default_factory=list)
