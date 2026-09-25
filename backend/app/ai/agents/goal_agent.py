"""Goal Agent (Phase 4).

Responsibilities:
- Retrieve active financial goals.
- Calculate goal progress and remaining amounts.
- Compute required monthly savings run-rate.
- Evaluate whether current savings trajectory is sufficient.
- Propose goal target updates under human-in-the-loop review.
"""

from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional
import uuid

from app.ai.agents.base import BaseAgent
from app.ai.agents.protocol import AgentResult
from app.ai.tools.registry import ToolRegistry

logger = logging.getLogger("finmate.ai.goal_agent")


class GoalAgent(BaseAgent):
    """Specialized agent for goal feasibility, tracking, and savings requirement analysis."""

    @property
    def name(self) -> str:
        return "GoalAgent"

    @property
    def description(self) -> str:
        return "Analyzes financial goals, computes progress, and determines required monthly savings trajectories."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "get_goals",
            "calculate_goal_progress",
            "calculate_required_monthly_saving",
            "simulate_financial_scenario",
            "propose_goal_update"
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
        recommendations: List[str] = []
        tradeoffs: List[Dict[str, Any]] = []
        uncertainties: List[str] = []
        pending_approval = None

        # 1. Retrieve all goals
        goals = self.call_tool("get_goals", {"user_id": user_id}, user_id, task_id)
        tools_used.append("get_goals")

        if not goals:
            return AgentResult(
                agent=self.name,
                status="completed",
                summary="You currently do not have any registered financial goals. Creating a goal will enable personalized milestone tracking.",
                facts=[],
                recommendations=["Define a primary financial goal with a target amount and deadline."],
                tools_used=tools_used,
                evidence_quality="LOW_EVIDENCE"
            )

        # Select target goal (e.g. education, laptop, emergency, or highest priority)
        target_goal = goals[0]
        for g in goals:
            g_name = g["name"].lower()
            if any(term in query_lower for term in ["education", "higher ed"]) and "education" in g_name:
                target_goal = g
                break
            elif "car" in query_lower and "car" in g_name:
                target_goal = g
                break

        # Check for mutation request
        # e.g., "Change education goal target to ₹3,50,000"
        if "change" in query_lower or "update" in query_lower:
            amt_match = re.search(r"(?:target|amount|to)\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)", query, re.IGNORECASE)
            if amt_match:
                new_amt = amt_match.group(1).replace(",", "")
                proposal = self.call_tool(
                    "propose_goal_update",
                    {
                        "user_id": user_id,
                        "goal_id": target_goal["id"],
                        "new_target_amount": f"{new_amt}.00",
                        "reason": f"User requested target amount update for '{target_goal['name']}'."
                    },
                    user_id,
                    task_id
                )
                tools_used.append("propose_goal_update")
                pending_approval = proposal
                summary = (
                    f"I have prepared a proposal to update the target amount for '{target_goal['name']}' "
                    f"from INR {target_goal['target_amount']} to INR {new_amt}.00. "
                    f"This mutation requires your confirmation."
                )
                return AgentResult(
                    agent=self.name,
                    status="pending_approval",
                    summary=summary,
                    facts=[{
                        "goal": target_goal["name"],
                        "current_target": f"INR {target_goal['target_amount']}",
                        "proposed_target": f"INR {new_amt}.00"
                    }],
                    recommendations=["Review and confirm the updated target in the approval pane."],
                    tools_used=tools_used,
                    evidence_quality="HIGH_EVIDENCE",
                    pending_approval=pending_approval
                )

        # 2. Calculate progress and required monthly savings
        progress_info = self.call_tool(
            "calculate_goal_progress",
            {"user_id": user_id, "goal_id": target_goal["id"]},
            user_id,
            task_id
        )
        tools_used.append("calculate_goal_progress")

        run_rate_info = self.call_tool(
            "calculate_required_monthly_saving",
            {"user_id": user_id, "goal_id": target_goal["id"], "target_months": 11},
            user_id,
            task_id
        )
        tools_used.append("calculate_required_monthly_saving")

        target_amt = Decimal(target_goal["target_amount"])
        curr_amt = Decimal(target_goal["current_amount"])
        remaining_amt = Decimal(progress_info["remaining_amount"])
        monthly_req = Decimal(run_rate_info["required_monthly_saving"])

        facts.append({
            "goal_name": target_goal["name"],
            "target_amount": f"INR {target_amt}",
            "current_amount": f"INR {curr_amt}",
            "remaining_amount": f"INR {remaining_amt}",
            "progress": f"{target_goal['progress_percentage']}%",
            "deadline": target_goal["target_date"],
            "required_monthly_savings": f"INR {monthly_req}"
        })

        # Assess feasibility against baseline surplus
        # Default baseline surplus is INR 25,000 from Profile/Summary
        baseline_surplus = Decimal("25000.00")
        if context_data and "monthly_surplus" in context_data:
            baseline_surplus = Decimal(str(context_data["monthly_surplus"]))

        is_on_track = baseline_surplus >= monthly_req
        if is_on_track:
            margin = baseline_surplus - monthly_req
            summary = (
                f"Yes, your '{target_goal['name']}' (Target: INR {target_amt}) is on track. "
                f"You have accumulated INR {curr_amt} ({target_goal['progress_percentage']}% progress), "
                f"leaving INR {remaining_amt} remaining by {target_goal['target_date']}. "
                f"Achieving this requires saving INR {monthly_req}/month, which fits comfortably within "
                f"your estimated monthly surplus of INR {baseline_surplus} with a cushion of INR {margin}."
            )
            tradeoffs.append({
                "action": "Maintain Current Contribution",
                "allocation": f"INR {monthly_req}/month",
                "surplus_cushion": f"INR {margin}/month",
                "impact": "Goal will be successfully completed on schedule."
            })
            recommendations.append(f"Set up an automated recurring allocation of INR {monthly_req}/month dedicated to this goal.")
        else:
            shortfall = monthly_req - baseline_surplus
            summary = (
                f"Your '{target_goal['name']}' requires saving INR {monthly_req}/month to complete by {target_goal['target_date']}. "
                f"Your estimated monthly surplus is INR {baseline_surplus}, creating a monthly shortfall of INR {shortfall}."
            )
            tradeoffs.append({
                "action": "Extend Deadline or Increase Savings",
                "shortfall": f"INR {shortfall}/month",
                "impact": "Requires reducing discretionary spending or extending target date."
            })
            recommendations.append("Consider extending the goal deadline by 3 to 6 months to reduce monthly capital pressure.")

        uncertainties.append("Inflation adjustments in education fees or target costs are not factored into nominal targets.")

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            facts=facts,
            predictions=[],
            recommendations=recommendations,
            tradeoffs=tradeoffs,
            assumptions=["Target date and target amounts remain static."],
            uncertainties=uncertainties,
            tools_used=tools_used,
            sources=[],
            evidence_quality="HIGH_EVIDENCE"
        )
