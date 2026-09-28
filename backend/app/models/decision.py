"""Financial Decision and Scenario SQLAlchemy ORM models."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import JSON, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Decision(Base, TimestampMixin):
    __tablename__ = "decisions"

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
    decision_type: Mapped[str] = mapped_column(String(50), nullable=False, default="purchase")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="simulated", nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="decisions")
    scenarios: Mapped[List["Scenario"]] = relationship(
        "Scenario",
        back_populates="decision",
        cascade="all, delete-orphan",
        order_by="Scenario.created_at"
    )

    __table_args__ = (
        Index("ix_decisions_user_created", "user_id", "created_at"),
    )


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("decisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Structured calculation results and explicit assumptions
    assumptions: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    financial_impact: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    goal_impact: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    savings_impact: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    cash_flow_impact: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    timeline_impact: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    warnings: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Relationships
    decision: Mapped["Decision"] = relationship("Decision", back_populates="scenarios")
