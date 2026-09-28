"""Deterministic Financial Decision and Scenario Engine.

ARCHITECTURAL PRINCIPLES:
1. Calculations MUST be 100% deterministic and mathematically authoritative.
2. Python `Decimal` is used exclusively for currency arithmetic. No floating-point math.
3. The LLM is NEVER the source of truth for arithmetic or calculations.
4. Assumptions and data limitations are explicitly declared, never concealed.
5. Decision support only: Never triggers automated payments or account mutations.
"""

import datetime
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.goal import Goal
from app.models.profile import FinancialProfile
from app.repositories.goal_repo import GoalRepository
from app.repositories.transaction_repo import TransactionRepository
from app.schemas.decision import (
    BaselineFinancialState,
    DecisionExplanation,
    DecisionSimulateRequest,
    DecisionSimulationResponse,
    FinancialImpact,
    GoalImpactDetail,
    ScenarioResponse,
)
from app.services.calculations import (
    calculate_goal_progress,
    calculate_savings,
    calculate_savings_rate,
    to_decimal,
)
from app.services.profile_service import ProfileService

TWO_PLACES = Decimal("0.01")
ONE_PLACE = Decimal("0.1")

DISCRETIONARY_CATEGORIES = {
    "dining", "food", "food & dining", "shopping", "entertainment",
    "lifestyle", "leisure", "travel", "subscriptions", "electronics",
    "personal care", "groceries & dining"
}


class FinancialDecisionEngine:
    """Authoritative calculation and scenario generation engine for financial decisions."""

    def __init__(self, db: Session):
        self.db = db
        self.profile_service = ProfileService(db)
        self.goal_repo = GoalRepository(db)
        self.tx_repo = TransactionRepository(db)

    def get_base_financial_state(self, user_id: uuid.UUID) -> BaselineFinancialState:
        """Retrieves and calculates deterministic baseline financial metrics from user ledger and profile."""
        profile: FinancialProfile = self.profile_service.get_or_create(user_id)

        income = to_decimal(profile.monthly_income)
        expenses = to_decimal(profile.monthly_fixed_expenses)
        savings = to_decimal(profile.current_savings)

        surplus = calculate_savings(income, expenses)
        savings_rate = calculate_savings_rate(income, surplus)

        # Savings coverage: months of current expenses covered by liquid savings
        savings_coverage: Optional[Decimal] = None
        if expenses > Decimal("0.00"):
            savings_coverage = (savings / expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)

        # Calculate user's actual discretionary spending from category breakdown
        discretionary_spending = Decimal("0.00")
        try:
            category_breakdown = self.tx_repo.get_category_breakdown(user_id, transaction_type="expense")
            for cat, cat_tot, _ in category_breakdown:
                if cat and cat.strip().lower() in DISCRETIONARY_CATEGORIES:
                    discretionary_spending += to_decimal(cat_tot)
        except Exception as exc:
            logger.debug("Could not compute category discretionary breakdown: %s", exc)

        # If no explicit transaction breakdown was found but ledger expenses exist
        if discretionary_spending == Decimal("0.00") and expenses > Decimal("0.00"):
            # Estimate flexible spending if total expenses exceed fixed expenses
            discretionary_spending = Decimal("0.00")

        has_sufficient = income > Decimal("0.00") and expenses > Decimal("0.00")
        notes: List[str] = [
            "Savings coverage is based on your current savings and average monthly expenses."
        ]
        if not has_sufficient:
            notes.append("Limited regular income or expense history recorded. Projections rely on current liquid reserves.")

        return BaselineFinancialState(
            monthly_income=income,
            monthly_expenses=expenses,
            monthly_surplus=surplus,
            monthly_discretionary_spending=discretionary_spending,
            current_savings=savings,
            available_cash=savings,
            savings_rate=savings_rate,
            emergency_buffer_months=savings_coverage,
            savings_coverage_months=savings_coverage,
            has_sufficient_data=has_sufficient,
            notes=notes,
        )

    def calculate_goal_impacts(
        self,
        user_id: uuid.UUID,
        baseline_surplus: Decimal,
        scenario_surplus_delta: Decimal,
        scenario_savings_delta: Decimal,
        affected_goal_id: Optional[uuid.UUID] = None,
    ) -> List[GoalImpactDetail]:
        """Calculates exact mathematical impacts on user goals for a specific scenario using transparent linear surplus modeling."""
        goals: List[Goal] = self.goal_repo.get_all_by_user(user_id)
        if not goals:
            return []

        results: List[GoalImpactDetail] = []
        today = datetime.date.today()

        for goal in goals:
            target = to_decimal(goal.target_amount)
            current = to_decimal(goal.current_amount)
            remaining = max(Decimal("0.00"), target - current)

            # Months remaining to target date
            months_to_target = 1
            if goal.target_date > today:
                months_to_target = max(
                    1,
                    (goal.target_date.year - today.year) * 12 + (goal.target_date.month - today.month)
                )

            # Required monthly contribution to hit target date exactly
            required_monthly = (remaining / Decimal(months_to_target)).quantize(
                TWO_PLACES, rounding=ROUND_CEILING
            ) if remaining > Decimal("0.00") else Decimal("0.00")

            # Current estimated contribution from surplus (distributed across active goals)
            active_count = Decimal(len(goals) or 1)
            baseline_alloc = (baseline_surplus / active_count).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            current_monthly_saving = max(Decimal("0.00"), baseline_alloc)

            # Baseline timeline to reach remaining amount
            baseline_months: Optional[int] = None
            if remaining <= Decimal("0.00"):
                baseline_months = 0
            elif current_monthly_saving > Decimal("0.00"):
                baseline_months = int(math.ceil(float(remaining / current_monthly_saving)))
            else:
                baseline_months = None

            # Scenario adjustments
            is_targeted = affected_goal_id is not None and goal.id == affected_goal_id
            scenario_alloc = max(
                Decimal("0.00"),
                (baseline_surplus + scenario_surplus_delta) / active_count
            ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            scenario_remaining = remaining
            # If scenario explicitly contributes to or withdraws from this goal's target
            if is_targeted and scenario_savings_delta != Decimal("0.00"):
                scenario_remaining = max(Decimal("0.00"), remaining - abs(scenario_savings_delta))

            scenario_months: Optional[int] = None
            timeline_diff: Optional[int] = None

            if scenario_remaining <= Decimal("0.00"):
                scenario_months = 0
                timeline_diff = -baseline_months if baseline_months is not None else 0
                summary = f"Goal '{goal.name}' estimated to be fully funded immediately under this scenario."
            elif scenario_alloc > Decimal("0.00"):
                scenario_months = int(math.ceil(float(scenario_remaining / scenario_alloc)))

                # If this is a general purchase tapping general savings reserve backing goals
                if scenario_savings_delta < Decimal("0.00") and not is_targeted:
                    recovery_months = int(
                        math.ceil(float(abs(scenario_savings_delta) / scenario_alloc))
                    ) if scenario_alloc > Decimal("0.00") else 0
                    scenario_months = (baseline_months or 0) + recovery_months

                if baseline_months is not None:
                    timeline_diff = scenario_months - baseline_months
                    if timeline_diff > 0:
                        summary = f"Estimated completion delayed by approximately {timeline_diff} month{'s' if timeline_diff != 1 else ''} based on current monthly surplus."
                    elif timeline_diff < 0:
                        summary = f"Estimated completion accelerated by approximately {abs(timeline_diff)} month{'s' if abs(timeline_diff) != 1 else ''} based on increased monthly allocation."
                    else:
                        summary = "Goal timeline estimated to remain on its baseline schedule based on current monthly surplus."
                else:
                    summary = f"Estimated completion: {scenario_months} months based on current monthly surplus."
            else:
                summary = "Monthly savings run-rate is insufficient to project a completion date without budget adjustments."

            results.append(
                GoalImpactDetail(
                    goal_id=goal.id,
                    goal_name=goal.name,
                    target_amount=target,
                    current_amount=current,
                    remaining_amount=remaining,
                    current_monthly_saving=current_monthly_saving,
                    required_monthly_saving=required_monthly,
                    estimated_months_to_goal=baseline_months,
                    scenario_months_to_goal=scenario_months,
                    timeline_difference_months=timeline_diff,
                    impact_summary=summary,
                )
            )

        return results

    def simulate_decision(
        self,
        user_id: uuid.UUID,
        request: DecisionSimulateRequest,
    ) -> DecisionSimulationResponse:
        """Simulates multi-scenario outcomes deterministically from the user's verified baseline state."""
        baseline = self.get_base_financial_state(user_id)
        amount = to_decimal(request.amount)
        decision_type = request.decision_type

        scenarios: List[ScenarioResponse] = []
        global_assumptions: List[str] = [
            f"Monthly income remains unchanged at ₹{baseline.monthly_income:,.2f}.",
            f"Recurring expenses remain unchanged at ₹{baseline.monthly_expenses:,.2f} unless modified by scenario.",
            "Zero loan debt financing and zero interest are assumed unless explicitly structured.",
            "No market capital appreciation or inflationary returns are assumed.",
            "Goal timelines are estimates based on your current monthly surplus and linear contribution without guarantees.",
        ]
        global_warnings: List[str] = []
        data_limitations: List[str] = list(baseline.notes)

        # -------------------------------------------------------------------
        # 1. PURCHASE / LARGE EXPENSE DECISION
        # -------------------------------------------------------------------
        if decision_type in ["purchase", "large_expense"]:
            scenarios = self._generate_purchase_scenarios(
                user_id, baseline, amount, request
            )
            if amount > baseline.current_savings:
                global_warnings.append(
                    f"Outlay of ₹{amount:,.2f} exceeds total recorded savings (₹{baseline.current_savings:,.2f}). "
                    "Executing this outright would require external financing or deplete all liquid reserves."
                )

        # -------------------------------------------------------------------
        # 2. SAVINGS DECISION (e.g. Save ₹X more per month)
        # -------------------------------------------------------------------
        elif decision_type == "saving":
            scenarios = self._generate_savings_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 3. EXPENSE CHANGE (e.g. Rent increase by ₹X)
        # -------------------------------------------------------------------
        elif decision_type == "expense_change":
            scenarios = self._generate_expense_change_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 4. GOAL CONTRIBUTION DECISION (e.g. Lump sum ₹X to goal)
        # -------------------------------------------------------------------
        elif decision_type == "goal_contribution":
            scenarios = self._generate_goal_contribution_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 5. DEBT PAYMENT DECISION
        # -------------------------------------------------------------------
        elif decision_type == "debt_payment":
            scenarios = self._generate_debt_payment_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 6. INVESTMENT DECISION (Informational only)
        # -------------------------------------------------------------------
        elif decision_type == "investment":
            scenarios = self._generate_investment_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 7. SUBSCRIPTION DECISION
        # -------------------------------------------------------------------
        elif decision_type == "subscription":
            scenarios = self._generate_subscription_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 8. INCOME CHANGE DECISION
        # -------------------------------------------------------------------
        elif decision_type == "income_change":
            scenarios = self._generate_income_change_scenarios(
                user_id, baseline, amount, request
            )

        # -------------------------------------------------------------------
        # 9. CUSTOM DECISION
        # -------------------------------------------------------------------
        else:
            scenarios = self._generate_custom_scenarios(
                user_id, baseline, amount, request
            )

        # Build Explanation
        explanation = self._build_explanation(request, baseline, scenarios)

        return DecisionSimulationResponse(
            decision_id=None,
            decision={
                "decision_type": request.decision_type,
                "title": request.title,
                "description": request.description,
                "amount": amount,
                "category": request.category,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
            baseline=baseline,
            scenarios=scenarios,
            explanation=explanation,
            assumptions=global_assumptions,
            warnings=global_warnings,
            data_limitations=data_limitations,
        )

    # =======================================================================
    # 1. PURCHASE SCENARIOS
    # =======================================================================
    def _generate_purchase_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for a discretionary or capital purchase."""
        scenarios: List[ScenarioResponse] = []

        # --- SCENARIO 1: Buy Now (Pay Immediately) ---
        new_savings_s1 = max(Decimal("0.00"), baseline.current_savings - amount)
        buffer_s1: Optional[Decimal] = None
        if baseline.monthly_expenses > Decimal("0.00"):
            buffer_s1 = (new_savings_s1 / baseline.monthly_expenses).quantize(
                ONE_PLACE, rounding=ROUND_HALF_UP
            )

        warnings_s1: List[str] = []
        if amount > baseline.current_savings:
            warnings_s1.append("Exceeds current savings; would exhaust all liquid reserves.")
        elif buffer_s1 is not None and buffer_s1 < Decimal("3.0"):
            warnings_s1.append(
                f"Savings coverage falls to {buffer_s1} months of current expenses (based on your current savings and average monthly expenses)."
            )

        goal_impacts_s1 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=baseline.monthly_surplus,
            scenario_surplus_delta=Decimal("0.00"),
            scenario_savings_delta=-amount,
            affected_goal_id=request.affected_goal_id,
        )

        scenarios.append(
            ScenarioResponse(
                name="Buy Now",
                description="Pay the full amount immediately from existing liquid cash reserves.",
                assumptions=[
                    "Entire purchase amount is debited from savings immediately.",
                    "Monthly cash flow surplus remains unchanged at baseline.",
                    "No credit or split-payment fee incurred.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s1,
                    savings_change=-amount,
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=-amount,
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=goal_impacts_s1,
                savings_impact={
                    "immediate_savings_drop": f"₹{amount:,.2f}",
                    "reserve_remaining": f"₹{new_savings_s1:,.2f}",
                },
                cash_flow_impact={
                    "monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}",
                    "cash_flow_change": "No change",
                },
                timeline_impact={
                    "delay_summary": "Liquid reserves reduced immediately; goals requiring this capital may experience timeline adjustments.",
                },
                warnings=warnings_s1,
            )
        )

        # --- SCENARIO 2: Wait & Save (Funded from Future Cash Flow) ---
        wait_months = 2
        if baseline.monthly_surplus > Decimal("0.00"):
            calc_months = int(math.ceil(float(amount / baseline.monthly_surplus)))
            wait_months = max(1, min(12, calc_months))

        accumulated = (baseline.monthly_surplus * Decimal(wait_months)).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        new_savings_s2 = baseline.current_savings + accumulated - amount
        buffer_s2: Optional[Decimal] = None
        if baseline.monthly_expenses > Decimal("0.00"):
            buffer_s2 = (new_savings_s2 / baseline.monthly_expenses).quantize(
                ONE_PLACE, rounding=ROUND_HALF_UP
            )

        goal_impacts_s2 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=baseline.monthly_surplus,
            scenario_surplus_delta=Decimal("0.00"),
            scenario_savings_delta=Decimal("0.00"),
            affected_goal_id=request.affected_goal_id,
        )

        scenarios.append(
            ScenarioResponse(
                name=f"Wait {wait_months} Month{'s' if wait_months != 1 else ''}",
                description=f"Accumulate purchase funds from monthly surplus over {wait_months} months to preserve baseline savings.",
                assumptions=[
                    f"Allocate monthly surplus toward this purchase for {wait_months} months.",
                    "Existing baseline liquid savings remains untouched.",
                    "Purchase takes place after sinking fund has been accumulated.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s2,
                    savings_change=new_savings_s2 - baseline.current_savings,
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_s2,
                    savings_coverage_months=buffer_s2,
                ),
                goal_impact=goal_impacts_s2,
                savings_impact={
                    "immediate_savings_drop": "₹0.00",
                    "reserve_preserved": f"₹{baseline.current_savings:,.2f}",
                },
                cash_flow_impact={
                    "monthly_dedication": f"₹{min(amount, baseline.monthly_surplus):,.2f}/month",
                    "cash_flow_after_wait": f"₹{baseline.monthly_surplus:,.2f}",
                },
                timeline_impact={
                    "delay_summary": f"Purchase is deferred by {wait_months} months; core goal timelines and savings coverage are fully protected.",
                },
                warnings=[],
            )
        )

        # --- SCENARIO 3: Buy Now + Trim Discretionary Outflows ---
        # Derive cut from user custom_parameters OR actual discretionary spending
        cut_amount: Decimal
        user_param = (request.custom_parameters or {}).get("discretionary_reduction_amount")
        user_pct = (request.custom_parameters or {}).get("discretionary_reduction_pct")

        if user_param is not None:
            cut_amount = to_decimal(user_param)
        elif user_pct is not None and baseline.monthly_discretionary_spending > Decimal("0.00"):
            cut_amount = (baseline.monthly_discretionary_spending * (to_decimal(user_pct) / Decimal("100.00"))).quantize(TWO_PLACES)
        elif baseline.monthly_discretionary_spending > Decimal("0.00"):
            # Base on actual discretionary spending: 25% of actual discretionary spending
            cut_amount = min(
                baseline.monthly_discretionary_spending,
                max(Decimal("1000.00"), (baseline.monthly_discretionary_spending * Decimal("0.25")).quantize(TWO_PLACES))
            )
        elif baseline.monthly_surplus > Decimal("0.00"):
            # Fallback to 20% of surplus
            cut_amount = min(
                Decimal("5000.00"),
                max(Decimal("1000.00"), (baseline.monthly_surplus * Decimal("0.20")).quantize(TWO_PLACES))
            )
        else:
            cut_amount = Decimal("1000.00")

        new_expenses_s3 = max(Decimal("0.00"), baseline.monthly_expenses - cut_amount)
        new_surplus_s3 = baseline.monthly_income - new_expenses_s3
        recovery_months = int(math.ceil(float(amount / new_surplus_s3))) if new_surplus_s3 > 0 else 6

        goal_impacts_s3 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=new_surplus_s3,
            scenario_surplus_delta=cut_amount,
            scenario_savings_delta=-amount,
            affected_goal_id=request.affected_goal_id,
        )

        disc_context = (
            f"Current discretionary spending: ₹{baseline.monthly_discretionary_spending:,.2f}/month."
            if baseline.monthly_discretionary_spending > Decimal("0.00")
            else "Discretionary reduction derived from available flexible cash margin."
        )

        scenarios.append(
            ScenarioResponse(
                name="Buy Now + Trim Discretionary Outflows",
                description=f"Proceed with purchase now, but trim discretionary spending by ₹{cut_amount:,.2f}/month to replenish cash reserves in ~{recovery_months} months.",
                assumptions=[
                    disc_context,
                    f"Discretionary spending reduced by ₹{cut_amount:,.2f}/month.",
                    f"Monthly surplus increases from ₹{baseline.monthly_surplus:,.2f} to ₹{new_surplus_s3:,.2f} (+₹{cut_amount:,.2f}/month additional cash flow).",
                    f"Cash reserve recovers back to baseline within approximately {recovery_months} months.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s1,
                    savings_change=-amount,
                    new_monthly_surplus=new_surplus_s3,
                    surplus_change=cut_amount,
                    new_monthly_expenses=new_expenses_s3,
                    expense_change=-cut_amount,
                    cash_position_change=-amount,
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=goal_impacts_s3,
                savings_impact={
                    "initial_drop": f"-₹{amount:,.2f}",
                    "monthly_recovery_speed": f"+₹{cut_amount:,.2f}/month extra savings",
                },
                cash_flow_impact={
                    "new_monthly_surplus": f"₹{new_surplus_s3:,.2f}",
                    "expense_reduction": f"₹{cut_amount:,.2f}/month",
                },
                timeline_impact={
                    "delay_summary": f"Faster reserve recovery ({recovery_months} months) minimizes long-term goal timeline impact.",
                },
                warnings=warnings_s1,
            )
        )

        return scenarios

    # =======================================================================
    # 2. SAVINGS SCENARIOS (Decision-Type Aware)
    # =======================================================================
    def _generate_savings_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for savings plans: Current Plan, Save Amount More, Save Stretch Target."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Current Plan
        goal_impacts_current = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=baseline.monthly_surplus,
            scenario_surplus_delta=Decimal("0.00"),
            scenario_savings_delta=Decimal("0.00"),
        )
        scenarios.append(
            ScenarioResponse(
                name="Current Savings Plan",
                description="Maintain existing monthly savings run-rate without modifications.",
                assumptions=["Savings rate remains at current baseline."],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=goal_impacts_current,
                savings_impact={"annual_savings": f"₹{(baseline.monthly_surplus * 12):,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Goal milestones continue on their current trajectory."},
                warnings=[],
            )
        )

        # Scenario 2: Save Target Amount More
        new_surplus = baseline.monthly_surplus + amount
        new_expenses = max(Decimal("0.00"), baseline.monthly_expenses - amount)
        goal_impacts_boosted = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=new_surplus,
            scenario_surplus_delta=amount,
            scenario_savings_delta=Decimal("0.00"),
        )
        buffer_boosted = (
            ((baseline.current_savings + (amount * 12)) / new_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if new_expenses > 0 else None
        )

        scenarios.append(
            ScenarioResponse(
                name=f"Boost Savings (+₹{amount:,.2f}/mo)",
                description=f"Increase monthly savings allocation by ₹{amount:,.2f}, adding ₹{(amount * 12):,.2f} in net wealth annually.",
                assumptions=[
                    f"Monthly spending is reduced by ₹{amount:,.2f}.",
                    f"New monthly surplus increases to ₹{new_surplus:,.2f}.",
                    f"Annual incremental savings equals ₹{(amount * 12):,.2f}.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings + (amount * 12),
                    savings_change=amount * 12,
                    new_monthly_surplus=new_surplus,
                    surplus_change=amount,
                    new_monthly_expenses=new_expenses,
                    expense_change=-amount,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_boosted,
                    savings_coverage_months=buffer_boosted,
                ),
                goal_impact=goal_impacts_boosted,
                savings_impact={
                    "incremental_12mo_savings": f"+₹{(amount * 12):,.2f}",
                    "new_savings_rate": f"{calculate_savings_rate(baseline.monthly_income, new_surplus)}%",
                },
                cash_flow_impact={
                    "new_monthly_surplus": f"₹{new_surplus:,.2f}",
                    "expense_ceiling": f"₹{new_expenses:,.2f}",
                },
                timeline_impact={
                    "summary": "Accelerates active goal completion milestones across your portfolio.",
                },
                warnings=[],
            )
        )

        # Scenario 3: Stretch Savings Target (Save 2x More)
        stretch_amount = amount * Decimal("2")
        new_surplus_s3 = baseline.monthly_surplus + stretch_amount
        new_expenses_s3 = max(Decimal("0.00"), baseline.monthly_expenses - stretch_amount)
        goal_impacts_stretch = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=new_surplus_s3,
            scenario_surplus_delta=stretch_amount,
            scenario_savings_delta=Decimal("0.00"),
        )
        buffer_stretch = (
            ((baseline.current_savings + (stretch_amount * 12)) / new_expenses_s3).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if new_expenses_s3 > 0 else None
        )

        scenarios.append(
            ScenarioResponse(
                name=f"Accelerate Savings (+₹{stretch_amount:,.2f}/mo - Stretch Target)",
                description=f"Stretch monthly savings allocation by ₹{stretch_amount:,.2f}/mo to maximize goal acceleration.",
                assumptions=[
                    f"Monthly spending reduced by ₹{stretch_amount:,.2f}/month.",
                    f"New monthly surplus expands to ₹{new_surplus_s3:,.2f}.",
                    f"Annual incremental savings equals ₹{(stretch_amount * 12):,.2f}.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings + (stretch_amount * 12),
                    savings_change=stretch_amount * 12,
                    new_monthly_surplus=new_surplus_s3,
                    surplus_change=stretch_amount,
                    new_monthly_expenses=new_expenses_s3,
                    expense_change=-stretch_amount,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_stretch,
                    savings_coverage_months=buffer_stretch,
                ),
                goal_impact=goal_impacts_stretch,
                savings_impact={
                    "incremental_12mo_savings": f"+₹{(stretch_amount * 12):,.2f}",
                    "new_savings_rate": f"{calculate_savings_rate(baseline.monthly_income, new_surplus_s3)}%",
                },
                cash_flow_impact={
                    "new_monthly_surplus": f"₹{new_surplus_s3:,.2f}",
                    "expense_ceiling": f"₹{new_expenses_s3:,.2f}",
                },
                timeline_impact={
                    "summary": "Substantially shortens milestone duration across all active targets.",
                },
                warnings=[] if new_expenses_s3 > 0 else ["High budget contraction requires strict spending adherence."],
            )
        )

        return scenarios

    # =======================================================================
    # 3. EXPENSE CHANGE SCENARIOS (Decision-Type Aware)
    # =======================================================================
    def _generate_expense_change_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for recurring expense adjustments (e.g. rent increase)."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Absorb Recurring Increase
        new_expenses_s1 = baseline.monthly_expenses + amount
        new_surplus_s1 = baseline.monthly_income - new_expenses_s1
        warnings_s1: List[str] = []
        if new_surplus_s1 < Decimal("0.00"):
            warnings_s1.append(
                f"Deficit alert: Monthly expenses (₹{new_expenses_s1:,.2f}) will exceed income (₹{baseline.monthly_income:,.2f}) by ₹{abs(new_surplus_s1):,.2f}/month."
            )

        goal_impacts_s1 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=new_surplus_s1,
            scenario_surplus_delta=-amount,
            scenario_savings_delta=Decimal("0.00"),
        )

        buffer_s1 = (
            (baseline.current_savings / new_expenses_s1).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if new_expenses_s1 > 0 else None
        )

        scenarios.append(
            ScenarioResponse(
                name="Absorb Expense Increase",
                description=f"Absorb recurring increase of ₹{amount:,.2f}/month without modifying other spending areas.",
                assumptions=[
                    f"Monthly expenses rise to ₹{new_expenses_s1:,.2f}.",
                    f"Monthly surplus contracts from ₹{baseline.monthly_surplus:,.2f} to ₹{new_surplus_s1:,.2f}.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=new_surplus_s1,
                    surplus_change=-amount,
                    new_monthly_expenses=new_expenses_s1,
                    expense_change=amount,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=goal_impacts_s1,
                savings_impact={"annual_surplus_loss": f"-₹{(amount * 12):,.2f}"},
                cash_flow_impact={
                    "remaining_monthly_surplus": f"₹{new_surplus_s1:,.2f}",
                },
                timeline_impact={
                    "summary": "Reduced surplus delays goal milestones unless offset by other budget reallocations.",
                },
                warnings=warnings_s1,
            )
        )

        # Scenario 2: Counterbalance with Discretionary Spending Cuts
        goal_impacts_s2 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=baseline.monthly_surplus,
            scenario_surplus_delta=Decimal("0.00"),
            scenario_savings_delta=Decimal("0.00"),
        )
        scenarios.append(
            ScenarioResponse(
                name="Counterbalance with Budget Cuts",
                description=f"Offset the ₹{amount:,.2f}/month increase by trimming flexible categories (e.g. Dining, Shopping).",
                assumptions=[
                    f"Cut flexible categories by ₹{amount:,.2f}/month.",
                    "Net monthly surplus remains protected at current baseline.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=goal_impacts_s2,
                savings_impact={"annual_surplus_protected": f"₹{(baseline.monthly_surplus * 12):,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Goal milestones proceed on their original target dates."},
                warnings=[],
            )
        )

        # Scenario 3: Increase Income Target to Offset
        scenarios.append(
            ScenarioResponse(
                name="Increase Monthly Income Target to Offset",
                description=f"Maintain current lifestyle and plan an additional ₹{amount:,.2f}/month in income (freelance, overtime, or raise).",
                assumptions=[
                    f"Income target increases by ₹{amount:,.2f}/month to match higher expense.",
                    "Net monthly savings and goal milestones remain completely undisturbed.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=new_expenses_s1,
                    expense_change=amount,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=goal_impacts_s2,
                savings_impact={"annual_savings_rate": "Preserved at current baseline."},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Goal milestones remain on schedule through offset earnings."},
                warnings=[],
            )
        )

        return scenarios

    # =======================================================================
    # 4. GOAL CONTRIBUTION SCENARIOS (Decision-Type Aware)
    # =======================================================================
    def _generate_goal_contribution_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for dedicated capital allocation to goals."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Immediate Lump Sum
        new_savings_s1 = max(Decimal("0.00"), baseline.current_savings - amount)
        buffer_s1 = (
            (new_savings_s1 / baseline.monthly_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if baseline.monthly_expenses > 0 else None
        )
        goal_impacts_s1 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=baseline.monthly_surplus,
            scenario_surplus_delta=Decimal("0.00"),
            scenario_savings_delta=amount,
            affected_goal_id=request.affected_goal_id,
        )

        scenarios.append(
            ScenarioResponse(
                name="Lump Sum Contribution Now",
                description=f"Allocate ₹{amount:,.2f} directly from current liquid savings to target goal.",
                assumptions=[
                    f"Directly advances goal target by ₹{amount:,.2f}.",
                    f"Liquid unallocated cash decreases from ₹{baseline.current_savings:,.2f} to ₹{new_savings_s1:,.2f}.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s1,
                    savings_change=-amount,
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=-amount,
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=goal_impacts_s1,
                savings_impact={"allocated_to_goal": f"₹{amount:,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Substantially accelerates or finishes target milestone timeline."},
                warnings=[] if amount <= baseline.current_savings else ["Amount exceeds available liquid reserves."],
            )
        )

        # Scenario 2: Phased Contribution Over 3 Months
        monthly_phase = (amount / Decimal("3")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        scenarios.append(
            ScenarioResponse(
                name="Spread Across 3 Months",
                description=f"Contribute ₹{monthly_phase:,.2f}/month over the next 3 months to preserve smoother liquidity.",
                assumptions=[
                    f"Allocate ₹{monthly_phase:,.2f} monthly for 3 consecutive months.",
                    "Minimizes sudden single-month reserve depletion.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings - amount,
                    savings_change=-amount,
                    new_monthly_surplus=max(Decimal("0.00"), baseline.monthly_surplus - monthly_phase),
                    surplus_change=-monthly_phase,
                    new_monthly_expenses=baseline.monthly_expenses + monthly_phase,
                    expense_change=monthly_phase,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=goal_impacts_s1,
                savings_impact={"phased_allocation": f"3 × ₹{monthly_phase:,.2f}"},
                cash_flow_impact={"temporary_surplus_adjustment": f"-₹{monthly_phase:,.2f}/month for 3 months"},
                timeline_impact={"summary": "Smooths milestone progress without sudden reserve shock."},
                warnings=[],
            )
        )

        # Scenario 3: Maintain Current Contribution Pace
        goal_impacts_s3 = self.calculate_goal_impacts(
            user_id=user_id,
            baseline_surplus=baseline.monthly_surplus,
            scenario_surplus_delta=Decimal("0.00"),
            scenario_savings_delta=Decimal("0.00"),
            affected_goal_id=request.affected_goal_id,
        )
        scenarios.append(
            ScenarioResponse(
                name="Maintain Current Contribution Pace",
                description="Keep current scheduled contribution pace without allocating additional lump sums.",
                assumptions=[
                    "Liquid savings reserves remain completely untouched.",
                    "Goal continues on its baseline surplus accumulation pace.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=goal_impacts_s3,
                savings_impact={"reserve_protected": f"₹{baseline.current_savings:,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Goal proceeds on its established target timeline."},
                warnings=[],
            )
        )

        return scenarios

    # =======================================================================
    # 5. DEBT PAYMENT SCENARIOS (Decision-Type Aware)
    # =======================================================================
    def _generate_debt_payment_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for debt repayment: Pay now, Pay partially, Maintain current repayment."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Clear Debt Now
        new_savings_s1 = max(Decimal("0.00"), baseline.current_savings - amount)
        buffer_s1 = (
            (new_savings_s1 / baseline.monthly_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if baseline.monthly_expenses > 0 else None
        )
        warnings_s1: List[str] = []
        if amount > baseline.current_savings:
            warnings_s1.append("Exceeds current savings; would exhaust all liquid reserves.")

        scenarios.append(
            ScenarioResponse(
                name="Clear Debt Now",
                description=f"Pay ₹{amount:,.2f} immediately from liquid savings to eliminate ongoing liability.",
                assumptions=[
                    f"Entire debt amount of ₹{amount:,.2f} is cleared immediately from savings.",
                    "Stops interest accumulation and eliminates recurring debt obligation.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s1,
                    savings_change=-amount,
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=-amount,
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=-amount,
                ),
                savings_impact={"debt_cleared": f"₹{amount:,.2f}", "new_savings": f"₹{new_savings_s1:,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Frees up long-term cash flow after short-term liquid reserve reduction."},
                warnings=warnings_s1,
            )
        )

        # Scenario 2: Pay 50% Lump Sum, Remainder Over 3 Months
        half_amount = (amount / Decimal("2")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        monthly_phase = (half_amount / Decimal("3")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        new_savings_s2 = max(Decimal("0.00"), baseline.current_savings - half_amount)
        buffer_s2 = (
            (new_savings_s2 / baseline.monthly_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if baseline.monthly_expenses > 0 else None
        )

        scenarios.append(
            ScenarioResponse(
                name="Pay Partially (50% Now, Remainder Over 3 Months)",
                description=f"Pay ₹{half_amount:,.2f} immediately, and clear remaining ₹{half_amount:,.2f} in 3 monthly installments.",
                assumptions=[
                    f"Lump sum payment of ₹{half_amount:,.2f} debited from savings.",
                    f"Monthly cash flow allocates ₹{monthly_phase:,.2f}/month for 3 months.",
                    "Balances debt reduction speed with liquidity buffer protection.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s2,
                    savings_change=-half_amount,
                    new_monthly_surplus=max(Decimal("0.00"), baseline.monthly_surplus - monthly_phase),
                    surplus_change=-monthly_phase,
                    new_monthly_expenses=baseline.monthly_expenses + monthly_phase,
                    expense_change=monthly_phase,
                    cash_position_change=-half_amount,
                    projected_emergency_buffer_months=buffer_s2,
                    savings_coverage_months=buffer_s2,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=max(Decimal("0.00"), baseline.monthly_surplus - monthly_phase),
                    scenario_surplus_delta=-monthly_phase,
                    scenario_savings_delta=-half_amount,
                ),
                savings_impact={"immediate_payment": f"₹{half_amount:,.2f}", "reserve_remaining": f"₹{new_savings_s2:,.2f}"},
                cash_flow_impact={"installment": f"₹{monthly_phase:,.2f}/month for 3 months"},
                timeline_impact={"summary": "Smooths debt payoff while keeping a higher savings cushion."},
                warnings=[],
            )
        )

        # Scenario 3: Maintain Current Scheduled Repayment
        scenarios.append(
            ScenarioResponse(
                name="Maintain Current Scheduled Repayment",
                description="Continue scheduled minimum or regular monthly debt payments without tapping liquid savings.",
                assumptions=[
                    "Liquid savings reserve remains 100% intact.",
                    "Repayment continues on scheduled loan terms.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"reserve_protected": f"₹{baseline.current_savings:,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "No disruption to savings coverage or active goal timelines."},
                warnings=[],
            )
        )

        return scenarios

    # =======================================================================
    # 6. INVESTMENT SCENARIOS (Informational Only - No fake returns)
    # =======================================================================
    def _generate_investment_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds informational investment allocation scenarios without fabricating market returns."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Current Position
        scenarios.append(
            ScenarioResponse(
                name="Current Position (No Additional Allocation)",
                description="Maintain current liquid cash reserves and existing investment positions without additional transfer.",
                assumptions=[
                    "Existing cash reserves and surplus remain at current baseline.",
                    "No additional capital transferred to investment vehicles.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"liquid_savings": f"₹{baseline.current_savings:,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Portfolio continues on baseline schedule."},
                warnings=[],
            )
        )

        # Scenario 2: Additional Contribution from Liquid Savings
        new_savings_s2 = max(Decimal("0.00"), baseline.current_savings - amount)
        buffer_s2 = (
            (new_savings_s2 / baseline.monthly_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if baseline.monthly_expenses > 0 else None
        )
        warnings_s2 = []
        if amount > baseline.current_savings:
            warnings_s2.append("Allocation exceeds total current liquid reserves.")

        scenarios.append(
            ScenarioResponse(
                name=f"Allocate ₹{amount:,.2f} from Liquid Savings",
                description=f"Transfer ₹{amount:,.2f} from liquid bank savings into target investment assets.",
                assumptions=[
                    f"₹{amount:,.2f} transferred from liquid bank savings.",
                    "Assumes 0% guaranteed capital appreciation. Evaluates cash liquidity impact only.",
                    "Funds transferred will not be immediately available as emergency cash.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=new_savings_s2,
                    savings_change=-amount,
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=-amount,
                    projected_emergency_buffer_months=buffer_s2,
                    savings_coverage_months=buffer_s2,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=-amount,
                ),
                savings_impact={"allocated_to_investment": f"₹{amount:,.2f}", "liquid_cushion_left": f"₹{new_savings_s2:,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Liquid reserves reduced in exchange for long-term invested assets."},
                warnings=warnings_s2,
            )
        )

        # Scenario 3: Systematic Allocation from Monthly Cash Flow
        sip_amount = (amount / Decimal("6")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        scenarios.append(
            ScenarioResponse(
                name="Systematic Allocation from Surplus (Over 6 Months)",
                description=f"Invest ₹{sip_amount:,.2f}/month over 6 months from ongoing surplus rather than drawing down liquid reserves.",
                assumptions=[
                    f"Allocate ₹{sip_amount:,.2f}/month from monthly surplus over 6 months.",
                    "Existing baseline liquid savings remains untouched.",
                    "No market return is fabricated; models cash flow commitment only.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=max(Decimal("0.00"), baseline.monthly_surplus - sip_amount),
                    surplus_change=-sip_amount,
                    new_monthly_expenses=baseline.monthly_expenses + sip_amount,
                    expense_change=sip_amount,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=max(Decimal("0.00"), baseline.monthly_surplus - sip_amount),
                    scenario_surplus_delta=-sip_amount,
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"liquid_savings_preserved": f"₹{baseline.current_savings:,.2f}"},
                cash_flow_impact={"sip_allocation": f"₹{sip_amount:,.2f}/month for 6 months"},
                timeline_impact={"summary": "Builds investment position gradually without liquid reserve disruption."},
                warnings=[],
            )
        )

        return scenarios

    # =======================================================================
    # 7. SUBSCRIPTION SCENARIOS (Decision-Type Aware)
    # =======================================================================
    def _generate_subscription_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for subscription additions: Add subscription, Do not add, Offset with discretionary cuts."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Add Subscription
        new_expenses_s1 = baseline.monthly_expenses + amount
        new_surplus_s1 = baseline.monthly_income - new_expenses_s1
        buffer_s1 = (
            (baseline.current_savings / new_expenses_s1).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if new_expenses_s1 > 0 else None
        )

        scenarios.append(
            ScenarioResponse(
                name="Add Subscription",
                description=f"Commit to recurring subscription cost of ₹{amount:,.2f}/month (₹{(amount * 12):,.2f}/year).",
                assumptions=[
                    f"Monthly recurring expense increases by ₹{amount:,.2f}.",
                    f"Annual cost equals ₹{(amount * 12):,.2f}.",
                    f"Monthly surplus contracts from ₹{baseline.monthly_surplus:,.2f} to ₹{new_surplus_s1:,.2f}.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=new_surplus_s1,
                    surplus_change=-amount,
                    new_monthly_expenses=new_expenses_s1,
                    expense_change=amount,
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=new_surplus_s1,
                    scenario_surplus_delta=-amount,
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"annual_cost": f"₹{(amount * 12):,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{new_surplus_s1:,.2f}"},
                timeline_impact={"summary": f"Reduces annual investable cash flow by ₹{(amount * 12):,.2f}."},
                warnings=[] if new_surplus_s1 >= 0 else ["Deficit alert: New expenses exceed monthly income."],
            )
        )

        # Scenario 2: Do Not Add Subscription
        scenarios.append(
            ScenarioResponse(
                name="Do Not Add Subscription",
                description="Keep current subscription footprint; avoid recurring expenditure.",
                assumptions=[
                    "Monthly expenses remain unchanged.",
                    "Saves ₹" + f"{(amount * 12):,.2f}/year in cash flow.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"annual_cash_saved": f"₹{(amount * 12):,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Milestones proceed on scheduled trajectory."},
                warnings=[],
            )
        )

        # Scenario 3: Offset by Trimming Discretionary Spending
        scenarios.append(
            ScenarioResponse(
                name="Offset Subscription by Trimming Flexible Budget",
                description=f"Add subscription, but offset the cost by reducing flexible categories by ₹{amount:,.2f}/month.",
                assumptions=[
                    f"Discretionary spending trimmed by ₹{amount:,.2f}/month to accommodate subscription.",
                    "Net monthly surplus remains unchanged at baseline.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"net_savings_protected": f"₹{(baseline.monthly_surplus * 12):,.2f}/year"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Goal milestones unaffected because net surplus is preserved."},
                warnings=[],
            )
        )

        return scenarios

    # =======================================================================
    # 8. INCOME CHANGE SCENARIOS (Decision-Type Aware)
    # =======================================================================
    def _generate_income_change_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Builds scenarios for income changes: Keep current spending, Save additional income, Increase goal allocation."""
        scenarios: List[ScenarioResponse] = []

        # Scenario 1: Keep Current Spending (Expand Surplus)
        new_surplus_s1 = baseline.monthly_surplus + amount
        buffer_s1 = (
            ((baseline.current_savings + (amount * 12)) / baseline.monthly_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
            if baseline.monthly_expenses > 0 else None
        )

        scenarios.append(
            ScenarioResponse(
                name="Keep Current Spending (Expand Monthly Surplus)",
                description=f"Absorb ₹{amount:,.2f}/month income increase directly into disposable cash flow.",
                assumptions=[
                    f"Monthly income increases by ₹{amount:,.2f}.",
                    "Recurring expenses stay constant at baseline.",
                    f"Monthly surplus expands to ₹{new_surplus_s1:,.2f}.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings + (amount * 12),
                    savings_change=amount * 12,
                    new_monthly_surplus=new_surplus_s1,
                    surplus_change=amount,
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=new_surplus_s1,
                    scenario_surplus_delta=amount,
                    scenario_savings_delta=Decimal("0.00"),
                ),
                savings_impact={"annual_incremental_savings": f"+₹{(amount * 12):,.2f}"},
                cash_flow_impact={"new_monthly_surplus": f"₹{new_surplus_s1:,.2f}"},
                timeline_impact={"summary": "Accelerates all financial targets through elevated cash generation."},
                warnings=[],
            )
        )

        # Scenario 2: Save Additional Income Directly to Liquid Reserves
        scenarios.append(
            ScenarioResponse(
                name="Direct Additional Income to Savings Reserve",
                description=f"Auto-transfer all ₹{amount:,.2f}/month of new income into liquid savings cushion.",
                assumptions=[
                    f"Automate monthly transfer of ₹{amount:,.2f} to savings.",
                    f"Builds an extra ₹{(amount * 12):,.2f} in liquid reserves within 12 months.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings + (amount * 12),
                    savings_change=amount * 12,
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=buffer_s1,
                    savings_coverage_months=buffer_s1,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=baseline.monthly_surplus,
                    scenario_surplus_delta=Decimal("0.00"),
                    scenario_savings_delta=amount * 12,
                ),
                savings_impact={"12mo_reserve_growth": f"+₹{(amount * 12):,.2f}"},
                cash_flow_impact={"disposable_margin": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Substantially strengthens financial resilience against unforeseen expenses."},
                warnings=[],
            )
        )

        # Scenario 3: Increase Goal Allocation
        scenarios.append(
            ScenarioResponse(
                name="Direct Additional Income to Goals",
                description=f"Allocate the entire ₹{amount:,.2f}/month increase toward active milestone goals.",
                assumptions=[
                    f"Allocate ₹{amount:,.2f}/month directly to goal targets.",
                    "Significantly shortens time required to achieve target milestones.",
                ],
                financial_impact=FinancialImpact(
                    new_savings=baseline.current_savings,
                    savings_change=Decimal("0.00"),
                    new_monthly_surplus=baseline.monthly_surplus,
                    surplus_change=Decimal("0.00"),
                    new_monthly_expenses=baseline.monthly_expenses,
                    expense_change=Decimal("0.00"),
                    cash_position_change=Decimal("0.00"),
                    projected_emergency_buffer_months=baseline.savings_coverage_months,
                    savings_coverage_months=baseline.savings_coverage_months,
                ),
                goal_impact=self.calculate_goal_impacts(
                    user_id=user_id,
                    baseline_surplus=new_surplus_s1,
                    scenario_surplus_delta=amount,
                    scenario_savings_delta=Decimal("0.00"),
                    affected_goal_id=request.affected_goal_id,
                ),
                savings_impact={"goal_acceleration_annual": f"+₹{(amount * 12):,.2f}"},
                cash_flow_impact={"monthly_surplus": f"₹{baseline.monthly_surplus:,.2f}"},
                timeline_impact={"summary": "Primary milestones achieved months ahead of original target schedule."},
                warnings=[],
            )
        )

        return scenarios

    # =======================================================================
    # 9. CUSTOM SCENARIOS
    # =======================================================================
    def _generate_custom_scenarios(
        self,
        user_id: uuid.UUID,
        baseline: BaselineFinancialState,
        amount: Decimal,
        request: DecisionSimulateRequest,
    ) -> List[ScenarioResponse]:
        """Dynamic scenario generator for custom decisions when sufficient data exists."""
        if amount <= Decimal("0.00"):
            return []

        # By default model as a capital event with 3 objective choices:
        # Option A: Outright outlay
        # Option B: Sinking fund accumulation
        # Option C: Reallocation
        return self._generate_purchase_scenarios(user_id, baseline, amount, request)

    # =======================================================================
    # EXPLANATION & WHAT CHANGES BUILDER
    # =======================================================================
    def _build_explanation(
        self,
        request: DecisionSimulateRequest,
        baseline: BaselineFinancialState,
        scenarios: List[ScenarioResponse],
    ) -> DecisionExplanation:
        """Constructs an objective, consumer-friendly explanation of trade-offs, separating changes from unchanged metrics."""
        amount = to_decimal(request.amount)
        title = request.title
        d_type = request.decision_type

        what_changes: List[str] = []
        what_stays: List[str] = [
            f"Monthly income: ₹{baseline.monthly_income:,.2f} (Unchanged)",
            f"Essential obligations: ₹{baseline.monthly_expenses:,.2f} (Unchanged)",
        ]

        # Use primary scenario (first option) to construct the explicit diff
        primary = scenarios[0] if scenarios else None

        if d_type in ["purchase", "large_expense"]:
            new_sav = max(Decimal("0.00"), baseline.current_savings - amount)
            new_cov = (
                (new_sav / baseline.monthly_expenses).quantize(ONE_PLACE, rounding=ROUND_HALF_UP)
                if baseline.monthly_expenses > 0 else None
            )
            what_changes.append(
                f"Savings: ₹{baseline.current_savings:,.2f} → ₹{new_sav:,.2f} (↓ ₹{amount:,.2f})"
            )
            if baseline.savings_coverage_months and new_cov:
                what_changes.append(
                    f"Savings coverage: {baseline.savings_coverage_months} → {new_cov} months of current expenses"
                )
            if primary and primary.goal_impact:
                top_goal = primary.goal_impact[0]
                if top_goal.timeline_difference_months and top_goal.timeline_difference_months > 0:
                    what_changes.append(
                        f"{top_goal.goal_name}: Estimated timeline +{top_goal.timeline_difference_months} month{'s' if top_goal.timeline_difference_months != 1 else ''}"
                    )
                else:
                    what_stays.append(f"{top_goal.goal_name} target milestone (On schedule)")

            what_stays.append(f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} (No change under immediate purchase)")

            trade_off = (
                f"Executing '{title}' immediately reduces liquid savings from ₹{baseline.current_savings:,.2f} "
                f"to ₹{new_sav:,.2f}. Because monthly surplus remains unchanged, the primary trade-off is reserve liquidity "
                f"rather than monthly cash flow. Waiting allows you to accumulate dedicated capital from future monthly surplus "
                "while keeping your current savings intact."
            )

        elif d_type == "saving":
            new_surp = baseline.monthly_surplus + amount
            what_changes.append(
                f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} → ₹{new_surp:,.2f} (+₹{amount:,.2f}/month)"
            )
            what_changes.append(
                f"Annual savings: +₹{(amount * 12):,.2f} in net wealth growth"
            )
            what_stays.append(f"Liquid savings: ₹{baseline.current_savings:,.2f} (Untouched)")

            trade_off = (
                f"Allocating an additional ₹{amount:,.2f}/month accelerates goal milestones and increases annual "
                "wealth accumulation, requiring an equivalent trim in flexible discretionary spending."
            )

        elif d_type == "expense_change":
            new_exp = baseline.monthly_expenses + amount
            new_surp = baseline.monthly_income - new_exp
            what_changes.append(
                f"Monthly recurring expenses: ₹{baseline.monthly_expenses:,.2f} → ₹{new_exp:,.2f} (+₹{amount:,.2f}/month)"
            )
            what_changes.append(
                f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} → ₹{new_surp:,.2f} (↓ ₹{amount:,.2f}/month)"
            )
            what_stays.append(f"Liquid savings: ₹{baseline.current_savings:,.2f} (Untouched)")
            what_stays.append(f"Monthly income: ₹{baseline.monthly_income:,.2f} (Unchanged)")

            trade_off = (
                f"An ongoing expense increase of ₹{amount:,.2f}/month reduces disposable cash flow. "
                "To prevent milestone delays, you can absorb the cost, offset it with discretionary cuts, or increase monthly income."
            )

        elif d_type == "subscription":
            new_exp = baseline.monthly_expenses + amount
            new_surp = baseline.monthly_income - new_exp
            what_changes.append(
                f"Monthly expenses: ₹{baseline.monthly_expenses:,.2f} → ₹{new_exp:,.2f} (+₹{amount:,.2f}/month)"
            )
            what_changes.append(
                f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} → ₹{new_surp:,.2f} (↓ ₹{amount:,.2f}/month)"
            )
            what_stays.append(f"Liquid savings: ₹{baseline.current_savings:,.2f} (Untouched)")

            trade_off = (
                f"A new subscription of ₹{amount:,.2f}/month equals ₹{(amount * 12):,.2f}/year. "
                "Review whether you want to absorb it from surplus or offset it by trimming other discretionary subscriptions."
            )

        elif d_type == "debt_payment":
            new_sav = max(Decimal("0.00"), baseline.current_savings - amount)
            what_changes.append(
                f"Liquid savings: ₹{baseline.current_savings:,.2f} → ₹{new_sav:,.2f} (↓ ₹{amount:,.2f})"
            )
            what_changes.append(
                f"Debt liability: Reduced by ₹{amount:,.2f}"
            )
            what_stays.append(f"Monthly income: ₹{baseline.monthly_income:,.2f} (Unchanged)")
            what_stays.append(f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} (No change)")

            trade_off = (
                f"Paying ₹{amount:,.2f} of debt eliminates liabilities and future interest, with the trade-off being "
                "an immediate reduction in liquid savings cushion."
            )

        elif d_type == "income_change":
            new_surp = baseline.monthly_surplus + amount
            what_changes.append(
                f"Monthly income: ₹{baseline.monthly_income:,.2f} → ₹{(baseline.monthly_income + amount):,.2f} (+₹{amount:,.2f}/month)"
            )
            what_changes.append(
                f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} → ₹{new_surp:,.2f} (+₹{amount:,.2f}/month)"
            )
            what_stays.append(f"Monthly expenses: ₹{baseline.monthly_expenses:,.2f} (Unchanged)")

            trade_off = (
                f"An additional ₹{amount:,.2f}/month in income creates new financial capacity. "
                "Trade-offs depend on whether you prioritize liquid buffer growth, goal acceleration, or lifestyle expansion."
            )

        elif d_type == "goal_contribution":
            new_sav = max(Decimal("0.00"), baseline.current_savings - amount)
            what_changes.append(
                f"Liquid savings: ₹{baseline.current_savings:,.2f} → ₹{new_sav:,.2f} (↓ ₹{amount:,.2f})"
            )
            what_changes.append(
                f"Target goal progress: Advanced by ₹{amount:,.2f}"
            )
            what_stays.append(f"Monthly income: ₹{baseline.monthly_income:,.2f} (Unchanged)")
            what_stays.append(f"Monthly surplus: ₹{baseline.monthly_surplus:,.2f} (Unchanged)")

            trade_off = (
                f"Contributing ₹{amount:,.2f} directly brings you closer to your milestone immediately, "
                "with the trade-off of a temporary contraction in unallocated liquid savings."
            )

        else:
            what_changes.append(f"Financial position shifts by ₹{amount:,.2f} according to selected option.")
            trade_off = "Review the side-by-side scenario comparison below to evaluate trade-offs against your goals."

        key_considerations: List[str] = [
            "Check that your savings coverage covers at least 3 months of expenses before large non-critical purchases.",
            "Compare the trade-off between immediate outlay and milestone timeline preservation.",
            "FinMate models the mathematical outcomes to assist your judgment; you remain in complete control of your decisions.",
        ]

        summary = f"Simulated financial impact of '{title}' (₹{amount:,.2f})."

        return DecisionExplanation(
            summary=summary,
            what_changes=what_changes,
            what_stays_unchanged=what_stays,
            trade_off_analysis=trade_off,
            key_considerations=key_considerations,
        )
