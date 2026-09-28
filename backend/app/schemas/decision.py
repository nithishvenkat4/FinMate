"""Pydantic schemas for Financial Decisions, What-If Simulations, and Scenario Comparisons."""

import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

DecisionType = Literal[
    "purchase",
    "goal_contribution",
    "large_expense",
    "debt_payment",
    "saving",
    "investment",
    "subscription",
    "income_change",
    "expense_change",
    "custom",
]


class BaselineFinancialState(BaseModel):
    monthly_income: Decimal = Field(default=Decimal("0.00"), description="Verified monthly income")
    monthly_expenses: Decimal = Field(default=Decimal("0.00"), description="Verified monthly expenses")
    monthly_surplus: Decimal = Field(default=Decimal("0.00"), description="Income minus expenses")
    monthly_discretionary_spending: Decimal = Field(default=Decimal("0.00"), description="Estimated flexible/discretionary monthly spending")
    current_savings: Decimal = Field(default=Decimal("0.00"), description="Current accumulated savings")
    available_cash: Decimal = Field(default=Decimal("0.00"), description="Liquid available cash")
    savings_rate: Decimal = Field(default=Decimal("0.00"), description="Savings percentage of income")
    emergency_buffer_months: Optional[Decimal] = Field(None, description="Months of expenses covered by savings (legacy alias)")
    savings_coverage_months: Optional[Decimal] = Field(None, description="Months of current expenses covered by savings")
    has_sufficient_data: bool = Field(True, description="Whether user data is sufficient for full modeling")
    notes: List[str] = Field(default_factory=list, description="Observations on base data quality")


class FinancialImpact(BaseModel):
    new_savings: Decimal = Field(description="Projected savings after decision")
    savings_change: Decimal = Field(description="Net difference in savings (new - current)")
    new_monthly_surplus: Decimal = Field(description="Projected monthly disposable surplus")
    surplus_change: Decimal = Field(description="Change in monthly disposable surplus")
    new_monthly_expenses: Decimal = Field(description="Projected monthly expenses")
    expense_change: Decimal = Field(description="Change in monthly recurring expenses")
    cash_position_change: Decimal = Field(description="Immediate cash change")
    projected_emergency_buffer_months: Optional[Decimal] = Field(None, description="Projected buffer months (legacy alias)")
    savings_coverage_months: Optional[Decimal] = Field(None, description="Projected savings coverage in months of expenses")


class GoalImpactDetail(BaseModel):
    goal_id: uuid.UUID
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    current_monthly_saving: Decimal
    required_monthly_saving: Decimal
    estimated_months_to_goal: Optional[int] = Field(None, description="Baseline months remaining")
    scenario_months_to_goal: Optional[int] = Field(None, description="Projected scenario months remaining")
    timeline_difference_months: Optional[int] = Field(None, description="Timeline delay or acceleration (+/- months)")
    impact_summary: str


class ScenarioResponse(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    assumptions: List[str] = Field(default_factory=list)
    financial_impact: FinancialImpact
    goal_impact: List[GoalImpactDetail] = Field(default_factory=list)
    savings_impact: Dict[str, Any] = Field(default_factory=dict)
    cash_flow_impact: Dict[str, Any] = Field(default_factory=dict)
    timeline_impact: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DecisionExplanation(BaseModel):
    summary: str
    what_changes: List[str] = Field(default_factory=list)
    what_stays_unchanged: List[str] = Field(default_factory=list)
    trade_off_analysis: str
    key_considerations: List[str] = Field(default_factory=list)


class DecisionSimulateRequest(BaseModel):
    decision_type: DecisionType = Field(default="purchase", description="Category of decision")
    amount: Decimal = Field(..., gt=0, description="Decision amount in INR (must be > 0)")
    title: str = Field(..., min_length=1, max_length=200, description="Title of planning decision")
    description: Optional[str] = Field(None, description="Contextual description")
    category: Optional[str] = Field(None, description="Expense or target category")
    affected_goal_id: Optional[uuid.UUID] = Field(None, description="Specific goal affected, if any")
    custom_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Scenario assumptions")
    save_to_history: bool = Field(default=False, description="Persist simulation record in history")


class DecisionSimulationResponse(BaseModel):
    decision_id: Optional[uuid.UUID] = None
    decision: Dict[str, Any]
    baseline: BaselineFinancialState
    scenarios: List[ScenarioResponse]
    explanation: DecisionExplanation
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_limitations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ScenarioCompareItem(BaseModel):
    metric: str
    baseline: str
    scenarios: Dict[str, str]


class ScenarioCompareRequest(BaseModel):
    simulation: DecisionSimulationResponse


class ScenarioCompareResponse(BaseModel):
    title: str
    comparison_matrix: List[ScenarioCompareItem]
    scenarios_summary: Dict[str, str]
    trade_off_summary: str


class DecisionListItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    title: str
    description: Optional[str] = None
    amount: Decimal
    category: Optional[str] = None
    status: str
    scenario_count: int
    created_at: datetime.datetime
    goal_impact_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DecisionDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    decision_type: str
    title: str
    description: Optional[str] = None
    amount: Decimal
    category: Optional[str] = None
    status: str
    scenarios: List[ScenarioResponse]
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
