"""Financial Decision and What-If Simulation API endpoints (Phase 5).

Endpoints:
- POST /api/v1/decisions/simulate: Authoritative deterministic simulation of financial decisions.
- POST /api/v1/decisions/compare: Side-by-side comparison matrix of decision scenarios.
- GET  /api/v1/decisions: Retrieve user's saved decision history.
- GET  /api/v1/decisions/{decision_id}: Fetch specific saved decision simulation.
- DELETE /api/v1/decisions/{decision_id}: Remove saved decision from history.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.decision_repo import DecisionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.decision import (
    DecisionDetailResponse,
    DecisionListItem,
    DecisionSimulateRequest,
    DecisionSimulationResponse,
    ScenarioCompareItem,
    ScenarioCompareRequest,
    ScenarioCompareResponse,
    ScenarioResponse,
)
from app.services.decision_engine import FinancialDecisionEngine

router = APIRouter(prefix="/decisions", tags=["Financial Decisions & Simulations"])


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.post(
    "/simulate",
    response_model=DecisionSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate financial decision outcomes across multiple deterministic scenarios",
)
def simulate_decision(
    payload: DecisionSimulateRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional user ID"),
    db: Session = Depends(get_db),
):
    """Executes a deterministic what-if evaluation of a financial decision.

    Computes cash position changes, savings buffer shifts, and goal milestone impacts
    across multiple scenarios without modifying the user's financial ledger.
    """
    uid = resolve_user_id(user_id, db)
    engine = FinancialDecisionEngine(db)
    simulation = engine.simulate_decision(user_id=uid, request=payload)

    if payload.save_to_history:
        repo = DecisionRepository(db)
        saved = repo.save_simulation(uid, simulation)
        simulation.decision_id = saved.id

    return simulation


@router.post(
    "/compare",
    response_model=ScenarioCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare scenarios side-by-side in a structured comparison matrix",
)
def compare_scenarios(payload: ScenarioCompareRequest):
    """Generates an objective side-by-side metric comparison table between baseline and all generated scenarios."""
    sim = payload.simulation
    base = sim.baseline

    matrix: List[ScenarioCompareItem] = []

    # 1. Immediate Cash Outlay
    matrix.append(
        ScenarioCompareItem(
            metric="Immediate Cash Outlay",
            baseline="₹0.00",
            scenarios={
                s.name: f"₹{abs(s.financial_impact.cash_position_change):,.2f}"
                if s.financial_impact.cash_position_change < 0
                else "₹0.00"
                for s in sim.scenarios
            },
        )
    )

    # 2. Remaining Liquid Savings
    matrix.append(
        ScenarioCompareItem(
            metric="Remaining Liquid Savings",
            baseline=f"₹{base.current_savings:,.2f}",
            scenarios={
                s.name: f"₹{s.financial_impact.new_savings:,.2f}"
                for s in sim.scenarios
            },
        )
    )

    # 3. Monthly Cashflow Surplus
    matrix.append(
        ScenarioCompareItem(
            metric="Monthly Surplus",
            baseline=f"₹{base.monthly_surplus:,.2f}",
            scenarios={
                s.name: f"₹{s.financial_impact.new_monthly_surplus:,.2f}"
                for s in sim.scenarios
            },
        )
    )

    # 4. Savings Coverage
    base_cov = base.savings_coverage_months or base.emergency_buffer_months
    base_buf_str = f"{base_cov} mo" if base_cov is not None else "N/A"
    matrix.append(
        ScenarioCompareItem(
            metric="Savings Coverage",
            baseline=base_buf_str,
            scenarios={
                s.name: f"{s.financial_impact.savings_coverage_months or s.financial_impact.projected_emergency_buffer_months} mo"
                if (s.financial_impact.savings_coverage_months or s.financial_impact.projected_emergency_buffer_months) is not None
                else "N/A"
                for s in sim.scenarios
            },
        )
    )

    # 5. Goal Timeline Impact
    def format_goal_impact(s: ScenarioResponse) -> str:
        if not s.goal_impact:
            return "No active goals affected"
        top_goal = s.goal_impact[0]
        if top_goal.timeline_difference_months is None or top_goal.timeline_difference_months == 0:
            return "On schedule"
        if top_goal.timeline_difference_months > 0:
            return f"+{top_goal.timeline_difference_months} mo delay"
        return f"{top_goal.timeline_difference_months} mo earlier"

    matrix.append(
        ScenarioCompareItem(
            metric="Goal Timeline Impact",
            baseline="Baseline Target",
            scenarios={s.name: format_goal_impact(s) for s in sim.scenarios},
        )
    )

    scenarios_summary = {
        s.name: s.description or s.name for s in sim.scenarios
    }

    return ScenarioCompareResponse(
        title=f"Scenario Comparison: {sim.decision.get('title', 'Financial Decision')}",
        comparison_matrix=matrix,
        scenarios_summary=scenarios_summary,
        trade_off_summary=sim.explanation.trade_off_analysis,
    )


@router.get(
    "",
    response_model=PaginatedResponse[DecisionListItem],
    status_code=status.HTTP_200_OK,
    summary="List saved decision simulations from history",
)
def list_decisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    uid = resolve_user_id(user_id, db)
    repo = DecisionRepository(db)
    skip = (page - 1) * page_size
    total = repo.count_by_user(uid)
    records = repo.get_all_by_user(uid, skip=skip, limit=page_size)

    items = []
    for d in records:
        goal_summary: Optional[str] = None
        if d.scenarios and d.scenarios[0].goal_impact:
            top_gi = d.scenarios[0].goal_impact[0]
            diff = top_gi.get("timeline_difference_months") if isinstance(top_gi, dict) else getattr(top_gi, "timeline_difference_months", None)
            if diff is not None:
                if diff > 0:
                    goal_summary = f"+{diff} mo"
                elif diff < 0:
                    goal_summary = f"{diff} mo"
                else:
                    goal_summary = "On schedule"
            else:
                goal_summary = top_gi.get("impact_summary") if isinstance(top_gi, dict) else getattr(top_gi, "impact_summary", None)

        items.append(
            DecisionListItem(
                id=d.id,
                user_id=d.user_id,
                decision_type=d.decision_type,
                title=d.title,
                description=d.description,
                amount=d.amount,
                category=d.category,
                status=d.status,
                scenario_count=len(d.scenarios),
                created_at=d.created_at,
                goal_impact_summary=goal_summary,
            )
        )

    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{decision_id}",
    response_model=DecisionDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details and scenarios of a specific saved decision",
)
def get_decision(
    decision_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    uid = resolve_user_id(user_id, db)
    repo = DecisionRepository(db)
    decision = repo.get_by_id_and_user(decision_id, uid)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision simulation '{decision_id}' not found.",
        )

    scenarios = [
        ScenarioResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            assumptions=s.assumptions or [],
            financial_impact=s.financial_impact,
            goal_impact=s.goal_impact or [],
            savings_impact=s.savings_impact or {},
            cash_flow_impact=s.cash_flow_impact or {},
            timeline_impact=s.timeline_impact or {},
            warnings=s.warnings or [],
        )
        for s in decision.scenarios
    ]

    return DecisionDetailResponse(
        id=decision.id,
        user_id=decision.user_id,
        decision_type=decision.decision_type,
        title=decision.title,
        description=decision.description,
        amount=decision.amount,
        category=decision.category,
        status=decision.status,
        scenarios=scenarios,
        metadata_json=decision.metadata_json,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
    )


@router.delete(
    "/{decision_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a saved decision simulation from history",
)
def delete_decision(
    decision_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    uid = resolve_user_id(user_id, db)
    repo = DecisionRepository(db)
    deleted = repo.delete_by_id_and_user(decision_id, uid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision simulation '{decision_id}' not found.",
        )
    return MessageResponse(message=f"Decision simulation '{decision_id}' deleted successfully.")
