"""FastAPI Endpoints for FinMate Multi-Agent Intelligence Layer (Phase 4).

Endpoints:
- POST /api/v1/agent/tasks: Submit a natural language question or financial scenario to the multi-agent orchestrator.
- GET  /api/v1/agent/tasks/{task_id}: Fetch task status, synthesis, facts, predictions, and trace.
- GET  /api/v1/agent/tasks/{task_id}/trace: Fetch step-by-step verified execution trace.
- GET  /api/v1/agent/approvals/pending: Fetch pending human approvals for AI proposals.
- POST /api/v1/agent/tasks/{task_id}/approve: Approve an AI-proposed mutating action.
- POST /api/v1/agent/tasks/{task_id}/reject: Reject an AI-proposed action (database remains unchanged).
- POST /api/v1/agent/tasks/{task_id}/cancel: Cancel an ongoing or pending task.
- GET  /api/v1/agent/tools: List all tools registered in the tool registry with permissions.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent import AgentApproval, AgentTask
from app.repositories.user_repo import UserRepository
from app.ai.orchestrator.orchestrator import AIOrchestrator
from app.ai.orchestrator.approval_engine import ApprovalEngine
from app.ai.tools.registry import ToolRegistry
from app.schemas.agent import (
    AgentTaskCreateRequest,
    AgentTaskResponse,
    AgentApprovalResponse,
    ApprovalActionRequest,
    ApprovalActionResponse,
    AgentToolInfo,
)

router = APIRouter(prefix="/agent", tags=["Multi-Agent Intelligence"])


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.post(
    "/tasks",
    response_model=AgentTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Coordinate specialized financial agents to analyze and explain user requests"
)
async def create_agent_task(
    payload: AgentTaskCreateRequest,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(payload.user_id, db)
    orchestrator = AIOrchestrator(db=db)
    result = await orchestrator.execute_task(
        query=payload.query,
        user_id=uid
    )
    return result


@router.get(
    "/tasks/{task_id}",
    response_model=AgentTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details, facts, predictions, and trace for a specific agent task"
)
def get_agent_task(
    task_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(user_id, db)
    stmt = select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == uid)
    task = db.scalars(stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent task '{task_id}' not found for user."
        )

    pending_app = None
    for a in task.approvals:
        if a.status == "pending":
            pending_app = {
                "approval_id": str(a.id),
                "action_type": a.action_type,
                "status": a.status,
                "target_id": a.target_id,
                "current_value": a.current_value,
                "proposed_value": a.proposed_value,
                "reason": a.reason,
                "expires_at": a.expires_at.isoformat(),
                "message": "Awaiting explicit user confirmation."
            }
            break

    return {
        "task_id": str(task.id),
        "status": task.status,
        "intent": task.intent,
        "summary": task.summary or "",
        "agents_used": task.agents_used,
        "tools_used": task.tools_used,
        "facts": task.facts,
        "predictions": task.predictions,
        "recommendations": task.recommendations,
        "tradeoffs": task.tradeoffs,
        "assumptions": task.assumptions,
        "uncertainties": task.uncertainties,
        "sources": task.sources,
        "evidence_quality": task.evidence_quality,
        "execution_trace": task.execution_trace,
        "pending_approval": pending_app
    }


@router.get(
    "/tasks/{task_id}/trace",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Fetch the verifiable step-by-step execution trace of an agent workflow"
)
def get_task_trace(
    task_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(user_id, db)
    stmt = select(AgentTask).where(AgentTask.id == task_id, AgentTask.user_id == uid)
    task = db.scalars(stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent task '{task_id}' not found."
        )
    return task.execution_trace


@router.get(
    "/approvals/pending",
    response_model=List[AgentApprovalResponse],
    status_code=status.HTTP_200_OK,
    summary="List all pending approvals for AI-proposed actions requiring human review"
)
def get_pending_approvals(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(user_id, db)
    engine = ApprovalEngine(db)
    approvals = engine.get_pending_approvals(uid)
    return [
        {
            "id": str(a.id),
            "task_id": str(a.task_id),
            "user_id": str(a.user_id),
            "agent_name": a.agent_name,
            "action_type": a.action_type,
            "target_id": a.target_id,
            "current_value": a.current_value,
            "proposed_value": a.proposed_value,
            "reason": a.reason,
            "status": a.status,
            "expires_at": a.expires_at.isoformat(),
            "created_at": a.created_at.isoformat()
        }
        for a in approvals
    ]


@router.post(
    "/tasks/{task_id}/approve",
    response_model=ApprovalActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve and apply an AI-proposed mutating action to the database"
)
def approve_task_action(
    task_id: uuid.UUID,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(payload.user_id, db)
    engine = ApprovalEngine(db)
    try:
        return engine.approve_action(task_id, payload.approval_id, uid)
    except TimeoutError as te:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(te))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post(
    "/tasks/{task_id}/reject",
    response_model=ApprovalActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject an AI-proposed mutating action (database remains untouched)"
)
def reject_task_action(
    task_id: uuid.UUID,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(payload.user_id, db)
    engine = ApprovalEngine(db)
    try:
        return engine.reject_action(task_id, payload.approval_id, uid)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Cancel a running or pending agent workflow"
)
def cancel_task(
    task_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    uid = resolve_user_id(user_id, db)
    engine = ApprovalEngine(db)
    try:
        return engine.cancel_task(task_id, uid)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.get(
    "/tools",
    response_model=List[AgentToolInfo],
    status_code=status.HTTP_200_OK,
    summary="List all registered tools, their authorization allowlists, and mutation flags"
)
def list_registered_tools():
    registry = ToolRegistry()
    return [
        {
            "name": t.name,
            "description": t.description,
            "allowed_agents": t.allowed_agents,
            "is_mutation": t.is_mutation,
            "requires_approval": t.requires_approval
        }
        for t in registry._tools.values()
    ]
