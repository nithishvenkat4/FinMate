"""Investment Asset SQLAlchemy ORM model."""

import uuid
from decimal import Decimal
from sqlalchemy import Numeric, String, Uuid, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Investment(Base, TimestampMixin):
    __tablename__ = "investments"

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
    asset_name: Mapped[str] = mapped_column(String(150), nullable=False)
    investment_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("1.0000"), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="investments")

    __table_args__ = (
        Index("ix_investments_user_type", "user_id", "investment_type"),
    )
