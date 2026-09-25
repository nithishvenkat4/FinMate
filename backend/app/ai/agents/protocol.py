"""Structured Agent Communication & Result Protocols (Phase 4).

Adheres to:
- Explicit typed communication between agents.
- Strict separation of FACT, PREDICTION, EXTERNAL KNOWLEDGE, RECOMMENDATION, and UNCERTAINTY.
- Execution traces and evidence contracts.
"""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """Explicit structured inter-agent communication message."""
    task_id: str
    from_agent: str
    to_agent: str
    message_type: str = "analysis_result"  # analysis_result, handoff_request, clarification_needed
    data: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Universal structured result contract returned by every specialized agent."""
    agent: str
    status: str = "completed"  # completed, pending_approval, failed, requires_handoff
    summary: str
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    predictions: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    tradeoffs: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_quality: str = "HIGH_EVIDENCE"  # HIGH_EVIDENCE, MEDIUM_EVIDENCE, LOW_EVIDENCE
    pending_approval: Optional[Dict[str, Any]] = None
    handoff_target: Optional[str] = None
    disagreement_note: Optional[str] = None


class ExecutionStep(BaseModel):
    """Single verified step in an agent workflow trace."""
    step_number: int
    agent: str
    action: str
    tool: Optional[str] = None
    status: str = "success"
    detail: str
    duration_ms: float = 0.0
