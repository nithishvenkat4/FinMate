"""Pydantic Request and Response Schemas for FinMate Agent System (Phase 4)."""

import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class AgentTaskCreateRequest(BaseModel):
    query: str = Field(..., min_length=2, description="User question or financial task prompt")
    user_id: Optional[uuid.UUID] = Field(None, description="Optional user ID; defaults to active demo user")


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    intent: str
    summary: str
    agents_used: List[str]
    tools_used: List[str]
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    predictions: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    tradeoffs: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_quality: str = "HIGH_EVIDENCE"
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    pending_approval: Optional[Dict[str, Any]] = None


class AgentApprovalResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    agent_name: str
    action_type: str
    target_id: str
    current_value: Dict[str, Any]
    proposed_value: Dict[str, Any]
    reason: str
    status: str
    expires_at: str
    created_at: str


class ApprovalActionRequest(BaseModel):
    approval_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None


class ApprovalActionResponse(BaseModel):
    approval_id: str
    task_id: str
    status: str
    action_type: Optional[str] = None
    executed_mutation: Optional[Dict[str, Any]] = None
    message: str


class AgentToolInfo(BaseModel):
    name: str
    description: str
    allowed_agents: List[str]
    is_mutation: bool
    requires_approval: bool
