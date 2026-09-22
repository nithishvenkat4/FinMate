"""Transaction Category SQLAlchemy ORM model."""

import datetime
import uuid
from typing import Optional
from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, utc_now


class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category_type: Mapped[str] = mapped_column(String(20), default="expense", nullable=False)  # 'income', 'expense', 'both'
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
