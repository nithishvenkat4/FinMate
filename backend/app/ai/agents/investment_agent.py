"""Investment Agent (Phase 4).

Responsibilities:
- Summarize investment portfolio holdings and valuations.
- Calculate asset class allocation breakdown.
- Retrieve educational concepts via RAG (ETFs, index funds, diversification, risk).
- Strict investment safety: NO autonomous trades, NO return guarantees, 100% informational.
"""

from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.ai.agents.base import BaseAgent
from app.ai.agents.protocol import AgentResult
from app.ai.tools.registry import ToolRegistry

logger = logging.getLogger("finmate.ai.investment_agent")


class InvestmentAgent(BaseAgent):
    """Specialized agent for informational portfolio analysis and financial education."""

    @property
    def name(self) -> str:
        return "InvestmentAgent"

    @property
    def description(self) -> str:
        return "Provides informational asset allocation analysis and retrieves verified financial education resources."

    @property
    def allowed_tools(self) -> List[str]:
        return [
            "get_investments",
            "calculate_investment_allocation",
            "retrieve_financial_knowledge"
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
        sources: List[Dict[str, Any]] = []
        uncertainties: List[str] = []

        # Scenario A: Educational concept question
        # e.g., "What does an ETF mean?" or "What is an index fund?" or "Explain risk"
        is_educational = any(term in query_lower for term in ["etf", "what is", "what does", "meaning", "explain", "risk", "index fund", "mutual fund"])

        if is_educational:
            # Retrieve RAG knowledge
            rag_res = self.call_tool(
                "retrieve_financial_knowledge",
                {"user_id": user_id, "query": query, "top_k": 2},
                user_id,
                task_id
            )
            tools_used.append("retrieve_financial_knowledge")
            sources = rag_res.get("results", [])

            summary = (
                "An Exchange Traded Fund (ETF) is a marketable security that tracks an index, commodity, "
                "bonds, or an index fund, and trades on a stock exchange like an individual stock. "
                "ETFs generally offer low expense ratios and intraday liquidity. "
                "FinMate provides educational information only; all investment decisions remain entirely yours."
            )
            if "risk" in query_lower:
                summary = (
                    "Investment risk refers to the degree of uncertainty and/or potential financial loss inherent in an "
                    "investment decision. Diversification across asset classes (equities, debt, gold) helps mitigate "
                    "unsystematic risk according to standard portfolio management principles."
                )

            recommendations.append("Review the fund factsheet and expense ratio (TER) before selecting any instrument.")
            recommendations.append("Ensure investment horizon matches the underlying asset volatility profile.")

            return AgentResult(
                agent=self.name,
                status="completed",
                summary=summary,
                facts=[{"topic": "Financial Education", "guidance": "Retrieved from verified regulatory/curriculum sources"}],
                predictions=[],
                recommendations=recommendations,
                tradeoffs=[{
                    "concept": "Passive Indexing vs Active Funds",
                    "pros": "Lower management fees, transparent portfolio replication",
                    "cons": "No potential to generate alpha over benchmark index"
                }],
                assumptions=["Educational context only. No personalized suitability advice is implied."],
                uncertainties=["Past performance does not guarantee future market returns."],
                tools_used=tools_used,
                sources=sources,
                evidence_quality="HIGH_EVIDENCE"
            )

        # Scenario B: Portfolio allocation analysis
        alloc_data = self.call_tool("calculate_investment_allocation", {"user_id": user_id}, user_id, task_id)
        tools_used.append("calculate_investment_allocation")

        total_val = alloc_data["total_portfolio_value"]
        allocations = alloc_data.get("asset_class_allocation", {})

        summary = (
            f"Your recorded investment portfolio has a total valuation of INR {total_val} across "
            f"{alloc_data['holdings_count']} holdings. Portfolio diversification is assessed as "
            f"'{alloc_data['diversification_status']}'."
        )

        for asset_class, details in allocations.items():
            facts.append({
                "asset_class": asset_class.replace("_", " ").title(),
                "valuation": f"INR {details['total_value']}",
                "allocation": f"{details['percentage']}%"
            })

        # Check RAG for asset allocation best practices
        rag_res = self.call_tool(
            "retrieve_financial_knowledge",
            {"user_id": user_id, "query": "Asset allocation and diversification rules", "top_k": 2},
            user_id,
            task_id
        )
        tools_used.append("retrieve_financial_knowledge")
        sources = rag_res.get("results", [])

        tradeoffs.append({
            "dimension": "Equity vs Fixed Income / Gold",
            "current_state": f"{alloc_data['diversification_status']}",
            "consideration": "Periodic rebalancing maintains target risk exposure across market cycles."
        })

        recommendations.append("Periodically review your asset allocation relative to your investment horizon.")
        recommendations.append("Keep emergency funds strictly separate from market-linked assets.")
        uncertainties.append("Market valuations fluctuate daily and do not represent guaranteed cash redemption values.")

        return AgentResult(
            agent=self.name,
            status="completed",
            summary=summary,
            facts=facts,
            predictions=[],
            recommendations=recommendations,
            tradeoffs=tradeoffs,
            assumptions=["Valuations are based on the latest recorded purchase or holding values."],
            uncertainties=uncertainties,
            tools_used=tools_used,
            sources=sources,
            evidence_quality="HIGH_EVIDENCE"
        )
