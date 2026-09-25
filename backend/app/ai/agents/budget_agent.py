"""Budget Agent (Phase 4).

Responsibilities:
- Analyze income, expenses, net savings, and savings rate.
- Identify budget pressure and category spending proportions.
- Integrate statistical expense forecasting (ML).
- Execute What-If scenario simulations (in-memory sandbox).
- Recognize when analysis impacts goals and signal orchestrator handoff.
"""

from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional
import uuid

from app.ai.agents.base import BaseAgent
from app.ai.agents.protocol import AgentResult
from app.ai.tools.registry import ToolRegistry

logger = logging.getLogger("finmate.ai.budget_agent")


class BudgetAgent(BaseAgent):
    """Specialized agent for cashflow, savings feasibility, and budget scenario simulations."""

    @property
    def name(self) -> str:
        return "BudgetAgent"

    @property
    def description(self) -> str:
        return "Analyzes income, expenses, savings rate, forecasts future outlays, and evaluates budget scenarios."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "get_financial_summary",
            "get_category_spending",
            "forecast_monthly_expenses",
            "simulate_financial_scenario"
        ]

    async def process(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        query: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        query_lower = query.lower()
        tools_used: List[str] = []
        facts: List[Dict[str, Any]] = []
        predictions: List[Dict[str, Any]] = []
        recommendations: List[str] = []
        tradeoffs: List[Dict[str, Any]] = []
        uncertainties: List[str] = []

        # 1. Fetch deterministic financial summary
        summary_data = self.call_tool("get_financial_summary", {"user_id": user_id}, user_id, task_id)
        tools_used.append("get_financial_summary")

        income = Decimal(summary_data["total_income"])
        expenses = Decimal(summary_data["total_expenses"])
        savings = Decimal(summary_data["net_savings"])
        savings_rate = summary_data["savings_rate"]

        facts.append({
            "metric": "Monthly Income",
            "value": f"INR {income}",
            "type": "Calculated Fact (Deterministic)"
        })
        facts.append({
            "metric": "Monthly Expenses",
            "value": f"INR {expenses}",
            "type": "Calculated Fact (Deterministic)"
        })
        facts.append({
            "metric": "Net Monthly Savings",
            "value": f"INR {savings}",
            "type": "Calculated Fact (Deterministic)"
        })
        facts.append({
            "metric": "Savings Rate",
            "value": f"{savings_rate}%",
            "type": "Calculated Fact (Deterministic)"
        })

        # Scenario A: What-If Simulation
        # e.g., "What if I spend ₹5,000 less next month?" or "What if I reduce entertainment spending by ₹2,000?"
        what_if_match = re.search(r"what\s+if\s+(?:i\s+)?(?:reduce|spend|cut)\s+(?:my\s+)?(?:monthly\s+)?([a-zA-Z\s]+?)\s*(?:by|less)?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)", query, re.IGNORECASE)
        reduced_match = re.search(r"(?:save|reduce|cut|spend)\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)\s*(?:less|more)?", query, re.IGNORECASE)

        if "what if" in query_lower or "simulate" in query_lower or ("reduce" in query_lower and any(c.isdigit() for c in query)):
            reduced_amount = "2000.00"
            if what_if_match:
                reduced_amount = what_if_match.group(2).replace(",", "")
            elif reduced_match:
                reduced_amount = reduced_match.group(1).replace(",", "")

            sim_result = self.call_tool(
                "simulate_financial_scenario",
                {
                    "user_id": user_id,
                    "reduced_expense": reduced_amount,
                    "simulation_months": 1
                },
                user_id,
                task_id
            )
            tools_used.append("simulate_financial_scenario")

            summary = (
                f"What-If Simulation Result: Reducing monthly expenses by INR {reduced_amount} "
                f"increases your net monthly savings from INR {sim_result['baseline_savings']} "
                f"to INR {sim_result['simulated_savings']} (new savings rate: {sim_result['simulated_savings_rate']}%). "
                f"{sim_result['disclaimer']}"
            )
            tradeoffs.append({
                "action": f"Reduce expenses by INR {reduced_amount}",
                "monthly_gain": f"+INR {reduced_amount}",
                "annualized_impact": f"+INR {Decimal(reduced_amount) * 12:.2f}",
                "verdict": sim_result["scenario_verdict"]
            })
            recommendations.append(
                f"Direct the additional INR {reduced_amount}/month surplus toward active goals or high-yield liquid emergency reserves."
            )
            return AgentResult(
                agent=self.name,
                status="completed",
                summary=summary,
                facts=facts,
                predictions=[],
                recommendations=recommendations,
                tradeoffs=tradeoffs,
                assumptions=["Simulation assumes income remains steady at baseline."],
                uncertainties=["Future discretionary expenses may experience seasonal variance."],
                tools_used=tools_used,
                sources=[],
                evidence_quality="HIGH_EVIDENCE"
            )

        # Scenario B: Can I save X amount / Am I spending too much on X / General cashflow
        # 2. Call ML Forecaster to project upcoming month expenses
        fc = self.call_tool("forecast_monthly_expenses", {"user_id": user_id, "months_ahead": 1}, user_id, task_id)
        tools_used.append("forecast_monthly_expenses")

        predictions.append({
            "metric": "Projected Next Month Expenses",
            "point_estimate": f"INR {fc['point_forecast']}",
            "confidence_interval_95": f"INR {fc['lower_bound_95']} – INR {fc['upper_bound_95']}",
            "trend": fc["trend"],
            "model": fc["model_name"]
        })

        # Check if user asked about saving a specific target amount, e.g. "Can I save ₹10,000 this month?"
        target_save_match = re.search(r"save\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)", query, re.IGNORECASE)
        if target_save_match:
            desired_savings = Decimal(target_save_match.group(1).replace(",", ""))
            is_feasible = savings >= desired_savings
            if is_feasible:
                margin = savings - desired_savings
                summary = (
                    f"Yes. Your current calculated monthly surplus is INR {savings} (based on income of INR {income} "
                    f"and expenses of INR {expenses}). Saving INR {desired_savings} is feasible with a safety cushion of INR {margin}."
                )
                recommendations.append(f"Automate transfer of INR {desired_savings} to your savings account on income deposit day.")
            else:
                deficit = desired_savings - savings
                summary = (
                    f"Saving INR {desired_savings} is currently challenging. Your current monthly surplus is INR {savings}, "
                    f"leaving a shortfall of INR {deficit}. Expense reductions would be needed to hit this target."
                )
                recommendations.append(f"Identify non-essential outlays to trim by INR {deficit} to achieve your savings goal.")
        else:
            summary = (
                f"Your current monthly surplus is INR {savings} with an active savings rate of {savings_rate}%. "
                f"Our statistical model forecasts next month expenses at INR {fc['point_forecast']} (trend: {fc['trend']})."
            )
            recommendations.append("Maintain emergency liquidity equal to at least 3-6 months of essential living expenses.")

        # Check for cross-domain goal dependency (Agent handoff signal)
        handoff_target = None
        if "goal" in query_lower or "laptop" in query_lower or "education" in query_lower:
            handoff_target = "GoalAgent"

        uncertainties.append("Unplanned discretionary spending or utility tariff shifts could alter surplus by ±8%.")

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            facts=facts,
            predictions=predictions,
            recommendations=recommendations,
            tradeoffs=tradeoffs,
            assumptions=["Income remains consistent with recent pay cycle."],
            uncertainties=uncertainties,
            tools_used=tools_used,
            sources=[],
            evidence_quality="HIGH_EVIDENCE",
            handoff_target=handoff_target
        )
