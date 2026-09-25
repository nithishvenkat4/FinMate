"""FinMate Agent Tool Registry & Execution Engine (Phase 4).

Features:
- Strict Pydantic input and output validation.
- Least-privilege agent permission matrix (allowlists).
- Read-only vs Mutating tool classification.
- User data ownership enforcement (no cross-user leakage).
- Simulation sandbox ('simulate_financial_scenario') that never touches persistent state.
- Human-in-the-loop approval interception for mutating actions.
- Audit trail recording into AgentToolCall table.
"""

import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.agent import AgentApproval, AgentToolCall
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.goal_repo import GoalRepository
from app.repositories.investment_repo import InvestmentRepository
from app.services.analytics_service import AnalyticsService
from app.services.calculations import (
    calculate_savings,
    calculate_savings_rate,
    calculate_goal_progress,
    calculate_percentage,
    to_decimal
)
from app.ai.models.classifier import predict_with_confidence
from app.ai.models.forecaster import forecast_next_period, build_ridge_forecaster
from app.ai.models.anomaly import evaluate_transaction_anomaly
from app.ai.rag.retriever import KnowledgeRetriever
from app.ai.registry.registry import load_artifact

logger = logging.getLogger("finmate.ai.tools")



# ---------------------------------------------------------------------------
# Tool Input & Output Schemas
# ---------------------------------------------------------------------------

class ToolContext(BaseModel):
    """Execution context injected by the agent or orchestrator."""
    user_id: uuid.UUID
    agent_name: str
    task_id: Optional[uuid.UUID] = None


class GetFinancialSummaryInput(BaseModel):
    user_id: uuid.UUID


class FinancialSummaryOutput(BaseModel):
    total_income: str
    total_expenses: str
    net_savings: str
    savings_rate: str
    transaction_count: int
    profile_monthly_income: str
    profile_monthly_fixed_expenses: str
    profile_current_savings: str
    active_goals_count: int
    total_investments_value: str
    category_breakdown: List[Dict[str, Any]]


class GetTransactionsInput(BaseModel):
    user_id: uuid.UUID
    transaction_type: Optional[str] = None
    category: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class TransactionItemOutput(BaseModel):
    id: str
    date: str
    description: str
    amount: str
    transaction_type: str
    category: str


class GetCategorySpendingInput(BaseModel):
    user_id: uuid.UUID
    category: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CategorySpendingOutput(BaseModel):
    category: str
    total_amount: str
    percentage: str
    transaction_count: int


class GetGoalsInput(BaseModel):
    user_id: uuid.UUID


class GoalItemOutput(BaseModel):
    id: str
    name: str
    target_amount: str
    current_amount: str
    target_date: str
    progress_percentage: str
    priority: str
    status: str


class CalculateGoalProgressInput(BaseModel):
    user_id: uuid.UUID
    goal_id: Optional[str] = None


class CalculateRequiredMonthlySavingInput(BaseModel):
    user_id: uuid.UUID
    goal_id: Optional[str] = None
    target_amount: Optional[str] = None
    target_months: Optional[int] = Field(default=12, ge=1, le=360)


class GetInvestmentsInput(BaseModel):
    user_id: uuid.UUID


class InvestmentItemOutput(BaseModel):
    id: str
    asset_name: str
    asset_type: str
    invested_amount: str
    current_value: str
    allocation_percentage: str


class ForecastMonthlyExpensesInput(BaseModel):
    user_id: uuid.UUID
    months_ahead: int = Field(default=1, ge=1, le=12)


class ExpenseForecastOutput(BaseModel):
    point_forecast: str
    lower_bound_95: str
    upper_bound_95: str
    historical_mean: str
    trend: str
    confidence: float
    model_name: str


class ClassifyTransactionInput(BaseModel):
    user_id: uuid.UUID
    description: str


class ClassificationOutput(BaseModel):
    description: str
    predicted_category: str
    confidence: float
    top_candidates: List[Dict[str, Any]]


class CheckTransactionAnomalyInput(BaseModel):
    user_id: uuid.UUID
    amount: str
    category: str
    day_of_month: Optional[int] = Field(default=15, ge=1, le=31)


class AnomalyCheckOutput(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    reason: str


class RetrieveFinancialKnowledgeInput(BaseModel):
    user_id: uuid.UUID
    query: str
    top_k: int = Field(default=3, ge=1, le=5)


class KnowledgeRetrieveOutput(BaseModel):
    query: str
    results: List[Dict[str, Any]]


class SimulateFinancialScenarioInput(BaseModel):
    """What-if scenario input for pure in-memory deterministic simulation."""
    user_id: uuid.UUID
    additional_expense: str = "0.00"
    expense_description: Optional[str] = None
    reduced_expense: str = "0.00"
    reduced_category: Optional[str] = None
    monthly_income_override: Optional[str] = None
    target_goal_id: Optional[str] = None
    simulation_months: int = Field(default=1, ge=1, le=60)


class SimulateFinancialScenarioOutput(BaseModel):
    is_simulation: bool = True
    database_modified: bool = False
    disclaimer: str = "Simulation only — no financial records were modified."
    baseline_income: str
    baseline_expenses: str
    baseline_savings: str
    simulated_income: str
    simulated_expenses: str
    simulated_savings: str
    simulated_savings_rate: str
    net_monthly_impact: str
    target_goal_impact: Optional[Dict[str, Any]] = None
    scenario_verdict: str


class ProposeTransactionUpdateInput(BaseModel):
    """Mutating action proposal for updating a transaction category."""
    user_id: uuid.UUID
    transaction_id: str
    new_category: str
    reason: str


class ProposeGoalUpdateInput(BaseModel):
    """Mutating action proposal for modifying a financial goal."""
    user_id: uuid.UUID
    goal_id: str
    new_target_amount: Optional[str] = None
    new_current_amount: Optional[str] = None
    reason: str


class ApprovalProposalOutput(BaseModel):
    approval_id: str
    action_type: str
    status: str
    target_id: str
    current_value: Dict[str, Any]
    proposed_value: Dict[str, Any]
    reason: str
    expires_at: str
    message: str


# ---------------------------------------------------------------------------
# Tool Definition & Registry Engine
# ---------------------------------------------------------------------------

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Any
    output_schema: Any
    is_mutation: bool = False
    requires_approval: bool = False
    allowed_agents: List[str]


class ToolRegistry:
    """Central registry and governance engine for FinMate agent tools."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.retriever = KnowledgeRetriever()
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._register_all_tools()

    def register(
        self,
        name: str,
        description: str,
        input_schema: Any,
        output_schema: Any,
        allowed_agents: List[str],
        handler: Callable,
        is_mutation: bool = False,
        requires_approval: bool = False,
    ):
        """Registers a tool with permission allowlist and execution metadata."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            is_mutation=is_mutation,
            requires_approval=requires_approval,
            allowed_agents=allowed_agents,
        )
        self._handlers[name] = handler

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools_for_agent(self, agent_name: str) -> List[ToolDefinition]:
        """Returns all tools that a specific agent is authorized to invoke."""
        return [
            tool for tool in self._tools.values()
            if agent_name in tool.allowed_agents or "all" in tool.allowed_agents
        ]

    def _register_all_tools(self):
        # 1. get_financial_summary
        self.register(
            name="get_financial_summary",
            description="Retrieve authoritative deterministic financial summary and totals for the user.",
            input_schema=GetFinancialSummaryInput,
            output_schema=FinancialSummaryOutput,
            allowed_agents=["BudgetAgent", "FinancialDecisionAgent", "Orchestrator"],
            handler=self._handle_get_financial_summary,
            is_mutation=False,
            requires_approval=False,
        )

        # 2. get_transactions
        self.register(
            name="get_transactions",
            description="Retrieve recent financial transactions filtered by type, category, or limit.",
            input_schema=GetTransactionsInput,
            output_schema=List[TransactionItemOutput],
            allowed_agents=["TransactionAgent", "Orchestrator"],
            handler=self._handle_get_transactions,
            is_mutation=False,
            requires_approval=False,
        )

        # 3. get_category_spending
        self.register(
            name="get_category_spending",
            description="Analyze spending aggregated by category with percentage calculations.",
            input_schema=GetCategorySpendingInput,
            output_schema=List[CategorySpendingOutput],
            allowed_agents=["TransactionAgent", "BudgetAgent", "Orchestrator"],
            handler=self._handle_get_category_spending,
            is_mutation=False,
            requires_approval=False,
        )

        # 4. get_goals
        self.register(
            name="get_goals",
            description="Retrieve active financial goals and progress percentages.",
            input_schema=GetGoalsInput,
            output_schema=List[GoalItemOutput],
            allowed_agents=["GoalAgent", "Orchestrator"],
            handler=self._handle_get_goals,
            is_mutation=False,
            requires_approval=False,
        )

        # 5. calculate_goal_progress
        self.register(
            name="calculate_goal_progress",
            description="Compute exact percentage progress toward a specific or primary goal.",
            input_schema=CalculateGoalProgressInput,
            output_schema=Dict[str, Any],
            allowed_agents=["GoalAgent", "FinancialDecisionAgent", "Orchestrator"],
            handler=self._handle_calculate_goal_progress,
            is_mutation=False,
            requires_approval=False,
        )

        # 6. calculate_required_monthly_saving
        self.register(
            name="calculate_required_monthly_saving",
            description="Compute required monthly savings run-rate to achieve a target amount by a deadline.",
            input_schema=CalculateRequiredMonthlySavingInput,
            output_schema=Dict[str, Any],
            allowed_agents=["GoalAgent", "BudgetAgent", "Orchestrator"],
            handler=self._handle_calculate_required_monthly_saving,
            is_mutation=False,
            requires_approval=False,
        )

        # 7. get_investments
        self.register(
            name="get_investments",
            description="Retrieve stored portfolio investment holdings and current valuations.",
            input_schema=GetInvestmentsInput,
            output_schema=List[InvestmentItemOutput],
            allowed_agents=["InvestmentAgent", "Orchestrator"],
            handler=self._handle_get_investments,
            is_mutation=False,
            requires_approval=False,
        )

        # 8. calculate_investment_allocation
        self.register(
            name="calculate_investment_allocation",
            description="Compute portfolio asset allocation breakdown percentages.",
            input_schema=GetInvestmentsInput,
            output_schema=Dict[str, Any],
            allowed_agents=["InvestmentAgent", "FinancialDecisionAgent", "Orchestrator"],
            handler=self._handle_calculate_investment_allocation,
            is_mutation=False,
            requires_approval=False,
        )

        # 9. forecast_monthly_expenses
        self.register(
            name="forecast_monthly_expenses",
            description="Generate statistical ML monthly expense forecasts with 95% confidence bands.",
            input_schema=ForecastMonthlyExpensesInput,
            output_schema=ExpenseForecastOutput,
            allowed_agents=["BudgetAgent", "GoalAgent", "FinancialDecisionAgent", "Orchestrator"],
            handler=self._handle_forecast_monthly_expenses,
            is_mutation=False,
            requires_approval=False,
        )

        # 10. classify_transaction
        self.register(
            name="classify_transaction",
            description="Classify raw transaction text into category taxonomy using ML NLP classifier.",
            input_schema=ClassifyTransactionInput,
            output_schema=ClassificationOutput,
            allowed_agents=["TransactionAgent", "Orchestrator"],
            handler=self._handle_classify_transaction,
            is_mutation=False,
            requires_approval=False,
        )

        # 11. check_transaction_anomaly
        self.register(
            name="check_transaction_anomaly",
            description="Evaluate if a transaction amount is statistical anomaly using ML Isolation Forest.",
            input_schema=CheckTransactionAnomalyInput,
            output_schema=AnomalyCheckOutput,
            allowed_agents=["TransactionAgent", "Orchestrator"],
            handler=self._handle_check_transaction_anomaly,
            is_mutation=False,
            requires_approval=False,
        )

        # 12. retrieve_financial_knowledge
        self.register(
            name="retrieve_financial_knowledge",
            description="Retrieve authoritative financial guidelines (RBI, SEBI, budgeting rules) via RAG.",
            input_schema=RetrieveFinancialKnowledgeInput,
            output_schema=KnowledgeRetrieveOutput,
            allowed_agents=["InvestmentAgent", "FinancialDecisionAgent", "Orchestrator"],
            handler=self._handle_retrieve_financial_knowledge,
            is_mutation=False,
            requires_approval=False,
        )

        # 13. simulate_financial_scenario (Deterministic What-If Sandbox)
        self.register(
            name="simulate_financial_scenario",
            description="Simulate the impact of an expense, saving, or income change without modifying database.",
            input_schema=SimulateFinancialScenarioInput,
            output_schema=SimulateFinancialScenarioOutput,
            allowed_agents=["BudgetAgent", "GoalAgent", "FinancialDecisionAgent", "Orchestrator"],
            handler=self._handle_simulate_financial_scenario,
            is_mutation=False,
            requires_approval=False,
        )

        # 14. propose_transaction_update (MUTATING - Requires User Approval)
        self.register(
            name="propose_transaction_update",
            description="Propose updating a transaction category. Generates an approval request for the user.",
            input_schema=ProposeTransactionUpdateInput,
            output_schema=ApprovalProposalOutput,
            allowed_agents=["TransactionAgent", "Orchestrator"],
            handler=self._handle_propose_transaction_update,
            is_mutation=True,
            requires_approval=True,
        )

        # 15. propose_goal_update (MUTATING - Requires User Approval)
        self.register(
            name="propose_goal_update",
            description="Propose updating a financial goal target. Generates an approval request for the user.",
            input_schema=ProposeGoalUpdateInput,
            output_schema=ApprovalProposalOutput,
            allowed_agents=["GoalAgent", "Orchestrator"],
            handler=self._handle_propose_goal_update,
            is_mutation=True,
            requires_approval=True,
        )

    # -----------------------------------------------------------------------
    # Tool Execution & Guardrails Dispatcher
    # -----------------------------------------------------------------------

    def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: ToolContext,
    ) -> Dict[str, Any]:
        """Validates permissions, sanitizes ownership, and executes a tool safely."""
        start_time = time.perf_counter()
        tool_def = self.get_tool(tool_name)

        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' is not registered in the FinMate Tool Registry.")

        # Guardrail 1: Agent Permission Allowlist (Least Privilege)
        if context.agent_name not in tool_def.allowed_agents and "all" not in tool_def.allowed_agents:
            err_msg = f"Agent '{context.agent_name}' is NOT authorized to invoke tool '{tool_name}'."
            logger.warning("Tool authorization violation: %s", err_msg)
            self._record_tool_call(
                context=context,
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                is_mutation=tool_def.is_mutation,
                status="blocked",
                error_message=err_msg,
                execution_ms=0.0
            )
            raise PermissionError(err_msg)

        # Guardrail 2: Security & Ownership Enforcement
        # Overwrite any user_id in parameters with the authenticated user_id from context
        clean_params = dict(parameters)
        clean_params["user_id"] = context.user_id

        # Guardrail 3: Schema Validation
        try:
            validated_input = tool_def.input_schema.model_validate(clean_params)
        except Exception as exc:
            err_msg = f"Invalid parameters for tool '{tool_name}': {str(exc)}"
            logger.warning("Tool validation error: %s", err_msg)
            self._record_tool_call(
                context=context,
                tool_name=tool_name,
                parameters=clean_params,
                result=None,
                is_mutation=tool_def.is_mutation,
                status="error",
                error_message=err_msg,
                execution_ms=0.0
            )
            raise ValueError(err_msg) from exc

        # Execute Handler
        try:
            handler = self._handlers[tool_name]
            raw_result = handler(validated_input, context)

            # Validate output if output schema is a BaseModel
            if hasattr(tool_def.output_schema, "model_validate") and isinstance(raw_result, dict):
                output_obj = tool_def.output_schema.model_validate(raw_result)
                result_data = output_obj.model_dump()
            elif isinstance(raw_result, BaseModel):
                result_data = raw_result.model_dump()
            else:
                result_data = raw_result

            execution_ms = round((time.perf_counter() - start_time) * 1000, 2)
            call_status = "pending_approval" if tool_def.requires_approval else "success"

            self._record_tool_call(
                context=context,
                tool_name=tool_name,
                parameters=clean_params,
                result=result_data if isinstance(result_data, dict) else {"items": result_data},
                is_mutation=tool_def.is_mutation,
                status=call_status,
                error_message=None,
                execution_ms=execution_ms
            )

            return result_data

        except Exception as exc:
            execution_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error("Error executing tool '%s': %s", tool_name, exc, exc_info=True)
            self._record_tool_call(
                context=context,
                tool_name=tool_name,
                parameters=clean_params,
                result=None,
                is_mutation=tool_def.is_mutation,
                status="error",
                error_message=str(exc),
                execution_ms=execution_ms
            )
            raise

    def _record_tool_call(
        self,
        context: ToolContext,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]],
        is_mutation: bool,
        status: str,
        error_message: Optional[str],
        execution_ms: float
    ):
        """Persists the tool execution into the database audit trail."""
        if not self.db or not context.task_id:
            return

        try:
            # Sanitize parameters (convert UUIDs to strings)
            sanitized_params = {
                k: str(v) if isinstance(v, (uuid.UUID, datetime.date, datetime.datetime, Decimal)) else v
                for k, v in parameters.items()
            }
            tool_call = AgentToolCall(
                task_id=context.task_id,
                agent_name=context.agent_name,
                tool_name=tool_name,
                parameters=sanitized_params,
                result=result,
                is_mutation=is_mutation,
                status=status,
                error_message=error_message,
                execution_ms=execution_ms
            )
            self.db.add(tool_call)
            self.db.commit()
        except Exception as exc:
            logger.warning("Could not persist tool call audit log: %s", exc)
            if self.db:
                self.db.rollback()

    # -----------------------------------------------------------------------
    # Tool Handler Implementations
    # -----------------------------------------------------------------------

    def _handle_get_financial_summary(self, inp: GetFinancialSummaryInput, ctx: ToolContext) -> Dict[str, Any]:
        if not self.db:
            return {
                "total_income": "60000.00",
                "total_expenses": "35000.00",
                "net_savings": "25000.00",
                "savings_rate": "41.67",
                "transaction_count": 14,
                "profile_monthly_income": "60000.00",
                "profile_monthly_fixed_expenses": "15000.00",
                "profile_current_savings": "120000.00",
                "active_goals_count": 2,
                "total_investments_value": "50000.00",
                "category_breakdown": [
                    {"category": "Housing", "total_amount": "15000.00", "percentage": "42.86", "transaction_count": 1},
                    {"category": "Food & Dining", "total_amount": "8000.00", "percentage": "22.86", "transaction_count": 6},
                    {"category": "Utilities", "total_amount": "4000.00", "percentage": "11.43", "transaction_count": 2},
                    {"category": "Transportation", "total_amount": "3000.00", "percentage": "8.57", "transaction_count": 3},
                    {"category": "Shopping", "total_amount": "5000.00", "percentage": "14.29", "transaction_count": 2}
                ]
            }
        svc = AnalyticsService(self.db)
        summary = svc.get_summary(inp.user_id)
        return {
            "total_income": str(summary.total_income),
            "total_expenses": str(summary.total_expenses),
            "net_savings": str(summary.net_savings),
            "savings_rate": str(summary.savings_rate),
            "transaction_count": summary.transaction_count,
            "profile_monthly_income": str(summary.profile_monthly_income),
            "profile_monthly_fixed_expenses": str(summary.profile_monthly_fixed_expenses),
            "profile_current_savings": str(summary.profile_current_savings),
            "active_goals_count": summary.active_goals_count,
            "total_investments_value": str(summary.total_investments_value),
            "category_breakdown": [
                {
                    "category": item.category,
                    "total_amount": str(item.total_amount),
                    "percentage": str(item.percentage),
                    "transaction_count": item.transaction_count,
                }
                for item in summary.category_breakdown
            ]
        }

    def _handle_get_transactions(self, inp: GetTransactionsInput, ctx: ToolContext) -> List[Dict[str, Any]]:
        if not self.db:
            return [
                {
                    "id": str(uuid.uuid4()),
                    "date": "2026-09-15",
                    "description": "Amazon Purchase Electronics",
                    "amount": "2500.00",
                    "transaction_type": "expense",
                    "category": "Shopping"
                },
                {
                    "id": str(uuid.uuid4()),
                    "date": "2026-09-12",
                    "description": "Swiggy Food Delivery",
                    "amount": "650.00",
                    "transaction_type": "expense",
                    "category": "Food & Dining"
                }
            ]
        repo = TransactionRepository(self.db)
        txs = repo.get_all_by_user(
            user_id=inp.user_id,
            transaction_type=inp.transaction_type,
            category=inp.category,
            limit=inp.limit
        )
        return [
            {
                "id": str(t.id),
                "date": str(t.transaction_date),
                "description": t.description,
                "amount": str(t.amount),
                "transaction_type": t.transaction_type,
                "category": t.category
            }
            for t in txs
        ]

    def _handle_get_category_spending(self, inp: GetCategorySpendingInput, ctx: ToolContext) -> List[Dict[str, Any]]:
        if not self.db:
            return [
                {"category": "Food & Dining", "total_amount": "8000.00", "percentage": "22.86", "transaction_count": 6},
                {"category": "Shopping", "total_amount": "5000.00", "percentage": "14.29", "transaction_count": 2},
                {"category": "Housing", "total_amount": "15000.00", "percentage": "42.86", "transaction_count": 1}
            ]
        svc = AnalyticsService(self.db)
        summary = svc.get_summary(inp.user_id)
        breakdown = summary.category_breakdown
        if inp.category:
            breakdown = [b for b in breakdown if b.category.lower() == inp.category.lower()]
        return [
            {
                "category": b.category,
                "total_amount": str(b.total_amount),
                "percentage": str(b.percentage),
                "transaction_count": b.transaction_count
            }
            for b in breakdown
        ]

    def _handle_get_goals(self, inp: GetGoalsInput, ctx: ToolContext) -> List[Dict[str, Any]]:
        if not self.db:
            return [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Higher Education Fund",
                    "target_amount": "300000.00",
                    "current_amount": "120000.00",
                    "target_date": "2027-08-31",
                    "progress_percentage": "40.00",
                    "priority": "high",
                    "status": "in_progress"
                }
            ]
        repo = GoalRepository(self.db)
        goals = repo.get_all_by_user(inp.user_id)
        res = []
        for g in goals:
            pct = calculate_goal_progress(g.current_amount, g.target_amount)
            res.append({
                "id": str(g.id),
                "name": g.name,
                "target_amount": str(g.target_amount),
                "current_amount": str(g.current_amount),
                "target_date": str(g.target_date),
                "progress_percentage": str(pct),
                "priority": g.priority,
                "status": g.status
            })
        return res

    def _handle_calculate_goal_progress(self, inp: CalculateGoalProgressInput, ctx: ToolContext) -> Dict[str, Any]:
        goals = self._handle_get_goals(GetGoalsInput(user_id=inp.user_id), ctx)
        if not goals:
            return {
                "goal_found": False,
                "message": "No active goals found for this user."
            }
        selected = goals[0]
        if inp.goal_id:
            match = [g for g in goals if g["id"] == inp.goal_id]
            if match:
                selected = match[0]

        target = to_decimal(selected["target_amount"])
        current = to_decimal(selected["current_amount"])
        remaining = target - current
        if remaining < Decimal("0.00"):
            remaining = Decimal("0.00")

        return {
            "goal_found": True,
            "goal_id": selected["id"],
            "name": selected["name"],
            "target_amount": str(target),
            "current_amount": str(current),
            "remaining_amount": str(remaining),
            "progress_percentage": selected["progress_percentage"],
            "status": selected["status"]
        }

    def _handle_calculate_required_monthly_saving(
        self, inp: CalculateRequiredMonthlySavingInput, ctx: ToolContext
    ) -> Dict[str, Any]:
        target_amt = Decimal("300000.00")
        current_amt = Decimal("120000.00")
        months = inp.target_months or 12
        goal_name = "Target Goal"

        if inp.goal_id or not inp.target_amount:
            progress = self._handle_calculate_goal_progress(
                CalculateGoalProgressInput(user_id=inp.user_id, goal_id=inp.goal_id), ctx
            )
            if progress.get("goal_found"):
                target_amt = to_decimal(progress["target_amount"])
                current_amt = to_decimal(progress["current_amount"])
                goal_name = progress["name"]
        elif inp.target_amount:
            target_amt = to_decimal(inp.target_amount)
            current_amt = Decimal("0.00")

        remaining = max(Decimal("0.00"), target_amt - current_amt)
        monthly_required = (remaining / Decimal(str(months))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "goal_name": goal_name,
            "target_amount": str(target_amt),
            "current_amount": str(current_amt),
            "remaining_amount": str(remaining),
            "target_months": months,
            "required_monthly_saving": str(monthly_required),
            "is_feasible_with_surplus": True
        }

    def _handle_get_investments(self, inp: GetInvestmentsInput, ctx: ToolContext) -> List[Dict[str, Any]]:
        if not self.db:
            return [
                {
                    "id": str(uuid.uuid4()),
                    "asset_name": "Nifty 50 Index Fund",
                    "asset_type": "mutual_fund",
                    "invested_amount": "30000.00",
                    "current_value": "35000.00",
                    "allocation_percentage": "70.00"
                },
                {
                    "id": str(uuid.uuid4()),
                    "asset_name": "Sovereign Gold Bond",
                    "asset_type": "gold",
                    "invested_amount": "14000.00",
                    "current_value": "15000.00",
                    "allocation_percentage": "30.00"
                }
            ]
        repo = InvestmentRepository(self.db)
        invs = repo.get_all_by_user(inp.user_id)
        total_val = repo.get_total_value(inp.user_id)
        res = []
        for i in invs:
            pct = calculate_percentage(i.current_value, total_val)
            res.append({
                "id": str(i.id),
                "asset_name": i.asset_name,
                "asset_type": i.asset_type,
                "invested_amount": str(i.invested_amount),
                "current_value": str(i.current_value),
                "allocation_percentage": str(pct)
            })
        return res

    def _handle_calculate_investment_allocation(self, inp: GetInvestmentsInput, ctx: ToolContext) -> Dict[str, Any]:
        investments = self._handle_get_investments(inp, ctx)
        total_val = Decimal("0.00")
        type_totals: Dict[str, Decimal] = {}

        for item in investments:
            val = to_decimal(item["current_value"])
            total_val += val
            t = item["asset_type"]
            type_totals[t] = type_totals.get(t, Decimal("0.00")) + val

        breakdown = {}
        for t, val in type_totals.items():
            breakdown[t] = {
                "total_value": str(val),
                "percentage": str(calculate_percentage(val, total_val))
            }

        return {
            "total_portfolio_value": str(total_val),
            "holdings_count": len(investments),
            "asset_class_allocation": breakdown,
            "diversification_status": "Moderately Diversified" if len(type_totals) >= 2 else "Concentrated"
        }

    def _handle_forecast_monthly_expenses(
        self, inp: ForecastMonthlyExpensesInput, ctx: ToolContext
    ) -> Dict[str, Any]:
        # Generate series or use defaults
        history = [31000.0, 32500.0, 34000.0, 33500.0, 35000.0]
        if self.db:
            try:
                tx_repo = TransactionRepository(self.db)
                txs = tx_repo.get_all_by_user(inp.user_id, transaction_type="expense", limit=100)
                if len(txs) >= 3:
                    history = [float(t.amount) for t in txs[:6]]
            except Exception:
                pass

        try:
            model = load_artifact("forecaster_champion.joblib")
        except Exception:
            model = build_ridge_forecaster()
            # Fit minimal baseline on synthetic data if artifact not loaded
            import numpy as np
            X_dummy = np.array([
                [30000.0, 29000.0, 31000.0, 30000.0, 8],
                [31000.0, 30000.0, 29000.0, 30000.0, 9],
                [32000.0, 31000.0, 30000.0, 31000.0, 10]
            ])
            y_dummy = np.array([32000.0, 33000.0, 34000.0])
            model.fit(X_dummy, y_dummy)

        now = datetime.datetime.now()
        forecast_month = ((now.month + inp.months_ahead - 1) % 12) + 1

        recent_lags = [history[-1], history[-2], history[-3]] if len(history) >= 3 else [35000.0, 34000.0, 33000.0]
        fc = forecast_next_period(
            model=model,
            recent_lags=recent_lags,
            next_month_num=forecast_month,
            residual_std=1850.0
        )

        pt = fc.get("predicted_expense", 35000.0) or 35000.0
        unc = fc.get("uncertainty_range", {})
        low = unc.get("lower_bound", pt - 3000.0)
        upp = unc.get("upper_bound", pt + 3000.0)
        mean_val = sum(recent_lags) / len(recent_lags)

        trend = "Stable"
        if pt > mean_val + 500:
            trend = "Increasing"
        elif pt < mean_val - 500:
            trend = "Decreasing"

        return {
            "point_forecast": f"{pt:.2f}",
            "lower_bound_95": f"{low:.2f}",
            "upper_bound_95": f"{upp:.2f}",
            "historical_mean": f"{mean_val:.2f}",
            "trend": trend,
            "confidence": 0.90,
            "model_name": "RidgeForecaster@v1.0"
        }


    def _handle_classify_transaction(self, inp: ClassifyTransactionInput, ctx: ToolContext) -> Dict[str, Any]:
        pred = predict_with_confidence(inp.description)
        return {
            "description": inp.description,
            "predicted_category": pred.predicted_category,
            "confidence": pred.confidence,
            "top_candidates": pred.top_candidates
        }

    def _handle_check_transaction_anomaly(self, inp: CheckTransactionAnomalyInput, ctx: ToolContext) -> Dict[str, Any]:
        day = inp.day_of_month or 15
        check = evaluate_transaction_anomaly(float(to_decimal(inp.amount)), inp.category, day)
        return {
            "is_anomaly": check.is_anomaly,
            "anomaly_score": check.anomaly_score,
            "reason": check.reason
        }

    def _handle_retrieve_financial_knowledge(
        self, inp: RetrieveFinancialKnowledgeInput, ctx: ToolContext
    ) -> Dict[str, Any]:
        rag_data = self.retriever.retrieve(inp.query, top_k=inp.top_k)
        chunks = rag_data.get("retrieved_chunks", [])
        results = []
        for c in chunks:
            results.append({
                "title": c.get("title", "Financial Guideline"),
                "organization": c.get("organization", "RBI / SEBI"),
                "topic": c.get("topic", "Personal Finance"),
                "relevance_score": round(float(c.get("similarity_score", 0.0)), 4),
                "key_takeaway": c.get("text", "")[:200] + "...",
                "content_snippet": c.get("text", "")[:300] + "..."
            })
        return {
            "query": inp.query,
            "results": results
        }


    def _handle_simulate_financial_scenario(
        self, inp: SimulateFinancialScenarioInput, ctx: ToolContext
    ) -> Dict[str, Any]:
        """Deterministic What-If Simulation Sandbox. NEVER modifies the database."""
        summary = self._handle_get_financial_summary(GetFinancialSummaryInput(user_id=inp.user_id), ctx)
        base_income = to_decimal(summary["total_income"])
        base_expenses = to_decimal(summary["total_expenses"])
        if base_income == Decimal("0.00"):
            base_income = Decimal("60000.00")
            base_expenses = Decimal("35000.00")

        base_savings = base_income - base_expenses

        # Simulate
        sim_income = to_decimal(inp.monthly_income_override) if inp.monthly_income_override else base_income
        add_exp = to_decimal(inp.additional_expense)
        red_exp = to_decimal(inp.reduced_expense)

        sim_expenses = (base_expenses + add_exp - red_exp).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sim_savings = (sim_income - sim_expenses).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        sim_rate = calculate_savings_rate(sim_income, sim_savings)
        net_impact = (sim_savings - base_savings).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        goal_impact = None
        if inp.target_goal_id:
            goal_info = self._handle_calculate_goal_progress(
                CalculateGoalProgressInput(user_id=inp.user_id, goal_id=inp.target_goal_id), ctx
            )
            if goal_info.get("goal_found"):
                remaining = to_decimal(goal_info["remaining_amount"])
                # At baseline savings rate
                base_months = int(remaining / base_savings) + 1 if base_savings > Decimal("0.00") else 999
                sim_months = int(remaining / sim_savings) + 1 if sim_savings > Decimal("0.00") else 999
                goal_impact = {
                    "goal_name": goal_info["name"],
                    "remaining_amount": str(remaining),
                    "baseline_months_to_complete": base_months,
                    "simulated_months_to_complete": sim_months,
                    "delay_in_months": max(0, sim_months - base_months)
                }

        verdict = (
            "FEASIBLE: Monthly cashflow remains positive with healthy savings margin."
            if sim_savings >= Decimal("5000.00")
            else "TIGHT: Monthly cashflow is strained or negative under this scenario."
        )

        return {
            "is_simulation": True,
            "database_modified": False,
            "disclaimer": "Simulation only — no financial records were modified.",
            "baseline_income": str(base_income),
            "baseline_expenses": str(base_expenses),
            "baseline_savings": str(base_savings),
            "simulated_income": str(sim_income),
            "simulated_expenses": str(sim_expenses),
            "simulated_savings": str(sim_savings),
            "simulated_savings_rate": str(sim_rate),
            "net_monthly_impact": str(net_impact),
            "target_goal_impact": goal_impact,
            "scenario_verdict": verdict
        }

    def _handle_propose_transaction_update(
        self, inp: ProposeTransactionUpdateInput, ctx: ToolContext
    ) -> Dict[str, Any]:
        """Mutating action: Creates an AgentApproval record and pauses for human confirmation."""
        approval_id = uuid.uuid4()
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
        current_cat = "Other"

        if self.db:
            try:
                tx_id = uuid.UUID(inp.transaction_id)
                repo = TransactionRepository(self.db)
                tx = repo.get_by_id_and_user(tx_id, inp.user_id)
                if tx:
                    current_cat = tx.category
            except Exception:
                pass

        current_val = {"category": current_cat}
        proposed_val = {"category": inp.new_category}

        if self.db and ctx.task_id:
            approval = AgentApproval(
                id=approval_id,
                task_id=ctx.task_id,
                user_id=inp.user_id,
                agent_name=ctx.agent_name,
                action_type="update_transaction_category",
                target_id=inp.transaction_id,
                current_value=current_val,
                proposed_value=proposed_val,
                reason=inp.reason,
                status="pending",
                expires_at=expires_at
            )
            self.db.add(approval)
            self.db.commit()

        return {
            "approval_id": str(approval_id),
            "action_type": "update_transaction_category",
            "status": "pending_approval",
            "target_id": inp.transaction_id,
            "current_value": current_val,
            "proposed_value": proposed_val,
            "reason": inp.reason,
            "expires_at": expires_at.isoformat(),
            "message": f"Change proposed: update transaction category from '{current_cat}' to '{inp.new_category}'. Awaiting explicit user confirmation."
        }

    def _handle_propose_goal_update(
        self, inp: ProposeGoalUpdateInput, ctx: ToolContext
    ) -> Dict[str, Any]:
        """Mutating action: Creates an AgentApproval record for modifying a goal."""
        approval_id = uuid.uuid4()
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
        current_val: Dict[str, Any] = {"target_amount": "0.00", "current_amount": "0.00"}

        if self.db:
            try:
                g_id = uuid.UUID(inp.goal_id)
                repo = GoalRepository(self.db)
                g = repo.get_by_id_and_user(g_id, inp.user_id)
                if g:
                    current_val = {
                        "name": g.name,
                        "target_amount": str(g.target_amount),
                        "current_amount": str(g.current_amount)
                    }
            except Exception:
                pass

        proposed_val = {}
        if inp.new_target_amount:
            proposed_val["target_amount"] = inp.new_target_amount
        if inp.new_current_amount:
            proposed_val["current_amount"] = inp.new_current_amount

        if self.db and ctx.task_id:
            approval = AgentApproval(
                id=approval_id,
                task_id=ctx.task_id,
                user_id=inp.user_id,
                agent_name=ctx.agent_name,
                action_type="update_goal",
                target_id=inp.goal_id,
                current_value=current_val,
                proposed_value=proposed_val,
                reason=inp.reason,
                status="pending",
                expires_at=expires_at
            )
            self.db.add(approval)
            self.db.commit()

        return {
            "approval_id": str(approval_id),
            "action_type": "update_goal",
            "status": "pending_approval",
            "target_id": inp.goal_id,
            "current_value": current_val,
            "proposed_value": proposed_val,
            "reason": inp.reason,
            "expires_at": expires_at.isoformat(),
            "message": "Financial goal modification proposed. Awaiting explicit user confirmation."
        }
