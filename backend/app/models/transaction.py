"""Transaction SQLAlchemy ORM model with data lineage and quality audit flags."""

import datetime
from decimal import Decimal
from typing import Optional
import uuid
from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

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
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("transaction_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    transaction_date: Mapped[datetime.date] = mapped_column(
        Date,
        default=datetime.date.today,
        nullable=False,
        index=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'income' or 'expense'
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Data Lineage & Auditability (Phase 2)
    source_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False, index=True)  # 'manual', 'csv_import', 'synthetic'
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    import_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid,
        ForeignKey("import_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    data_quality_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON-encoded array of warning codes

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    category_rel: Mapped[Optional["TransactionCategory"]] = relationship("TransactionCategory")
    import_record: Mapped[Optional["ImportRecord"]] = relationship("ImportRecord", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_category", "user_id", "category"),
        Index("ix_transactions_user_dedup", "user_id", "transaction_date", "amount", "description"),
    )
