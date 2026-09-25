"""Agentic Intelligence SQLAlchemy ORM models (Phase 4).

Models:
- AgentTask: Records the lifecycle, intent, status, structured facts, and execution trace of an agentic workflow.
- AgentApproval: Human-in-the-loop approval record for mutating actions proposed by agents.
- AgentToolCall: Audit trail of every tool invoked during workflow execution.
"""

import datetime
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class AgentTask(Base, TimestampMixin):
    """Represents an agentic workflow task initiated by a user or orchestrator."""
    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(100), nullable=False, default="UNKNOWN", index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    # statuses: pending, running, waiting_for_user, completed, failed, cancelled, timed_out

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured, partitioned evidence contracts
    facts: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    predictions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    recommendations: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    tradeoffs: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    assumptions: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    uncertainties: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    sources: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Real, un-fabricated execution trace
    execution_trace: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    agents_used: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    tools_used: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Disagreement & escalation metadata
    disagreements: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    evidence_quality: Mapped[str] = mapped_column(String(50), default="HIGH_EVIDENCE", nullable=False)

    # Relationships
    user = relationship("User", backref="agent_tasks")
    approvals = relationship("AgentApproval", back_populates="task", cascade="all, delete-orphan")
    tool_calls = relationship("AgentToolCall", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AgentTask {self.id} user={self.user_id} intent={self.intent} status={self.status}>"


class AgentApproval(Base, TimestampMixin):
    """Human-in-the-loop approval record for mutating actions proposed by agents."""
    __tablename__ = "agent_approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # action types: update_transaction_category, update_goal, etc.

    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    proposed_value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    # statuses: pending, approved, rejected, expired, cancelled

    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    task = relationship("AgentTask", back_populates="approvals")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AgentApproval {self.id} action={self.action_type} status={self.status}>"


class AgentToolCall(Base):
    """Audit log of individual tool executions across all specialized agents."""
    __tablename__ = "agent_tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("agent_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_mutation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)
    # statuses: success, error, blocked, pending_approval
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False
    )

    task = relationship("AgentTask", back_populates="tool_calls")

    def __repr__(self) -> str:
        return f"<AgentToolCall {self.id} agent={self.agent_name} tool={self.tool_name} status={self.status}>"
