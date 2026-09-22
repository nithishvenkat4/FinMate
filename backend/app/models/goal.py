"""Financial Goal SQLAlchemy ORM model."""

import datetime
import uuid
from decimal import Decimal
from sqlalchemy import Date, Numeric, String, Uuid, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

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
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    target_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="goals")

    __table_args__ = (
        Index("ix_goals_user_target_date", "user_id", "target_date"),
    )
