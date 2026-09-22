"""AI Agent Orchestrator placeholder."""

from typing import List
from app.ai.agents.agent_base import BaseSpecializedAgent, AgentContext, AgentResponse
from app.ai.agents.specialized_agents import (
    TransactionAgent,
    BudgetAgent,
    GoalAgent,
    InvestmentAgent,
    FinancialDecisionAgent,
)


class AIOrchestrator:
    """Coordinates specialized financial agents and ensures human-in-the-loop review.

    This orchestrator is explicitly deferred to Phase 9.
    """

    def __init__(self):
        self.agents: List[BaseSpecializedAgent] = [
            TransactionAgent(),
            BudgetAgent(),
            GoalAgent(),
            InvestmentAgent(),
            FinancialDecisionAgent(),
        ]

    async def coordinate(self, context: AgentContext) -> List[AgentResponse]:
        """Future coordination entry point."""
        results = []
        for agent in self.agents:
            res = await agent.analyze(context)
            results.append(res)
        return results
