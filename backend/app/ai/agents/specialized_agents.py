"""Specialized AI Agents placeholders for future phases."""

from app.ai.agents.agent_base import BaseSpecializedAgent, AgentContext, AgentResponse


class TransactionAgent(BaseSpecializedAgent):
    @property
    def name(self) -> str:
        return "TransactionAgent"

    async def analyze(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            insights="TransactionAgent placeholder: Ready for Phase 4 transaction intelligence & categorization.",
            deterministic_grounding={"status": "deferred_to_phase_4"},
            requires_user_approval=True
        )


class BudgetAgent(BaseSpecializedAgent):
    @property
    def name(self) -> str:
        return "BudgetAgent"

    async def analyze(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            insights="BudgetAgent placeholder: Ready for Phase 8 budgeting and cashflow forecasting.",
            deterministic_grounding={"status": "deferred_to_phase_8"},
            requires_user_approval=True
        )


class GoalAgent(BaseSpecializedAgent):
    @property
    def name(self) -> str:
        return "GoalAgent"

    async def analyze(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            insights="GoalAgent placeholder: Ready for Phase 8 goal feasibility tracking.",
            deterministic_grounding={"status": "deferred_to_phase_8"},
            requires_user_approval=True
        )


class InvestmentAgent(BaseSpecializedAgent):
    @property
    def name(self) -> str:
        return "InvestmentAgent"

    async def analyze(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            insights="InvestmentAgent placeholder: Ready for Phase 8 portfolio allocation analysis.",
            deterministic_grounding={"status": "deferred_to_phase_8"},
            requires_user_approval=True
        )


class FinancialDecisionAgent(BaseSpecializedAgent):
    @property
    def name(self) -> str:
        return "FinancialDecisionAgent"

    async def analyze(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            insights="FinancialDecisionAgent placeholder: Synthesizes cross-domain multi-agent proposals for human review.",
            deterministic_grounding={"status": "deferred_to_phase_9"},
            requires_user_approval=True
        )
