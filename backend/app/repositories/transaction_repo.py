"""Transaction repository module."""

import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def get_by_id_and_user(self, id: uuid.UUID, user_id: uuid.UUID) -> Optional[Transaction]:
        stmt = select(Transaction).where(Transaction.id == id, Transaction.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_all_by_user(
        self,
        user_id: uuid.UUID,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        stmt = select(Transaction).where(Transaction.user_id == user_id)

        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type.lower())
        if category:
            stmt = stmt.where(Transaction.category == category)
        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)

        stmt = stmt.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_by_user(
        self,
        user_id: uuid.UUID,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime.date] = None,
        end_date: Optional[datetime.date] = None,
    ) -> int:
        stmt = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type.lower())
        if category:
            stmt = stmt.where(Transaction.category == category)
        if start_date:
            stmt = stmt.where(Transaction.transaction_date >= start_date)
        if end_date:
            stmt = stmt.where(Transaction.transaction_date <= end_date)
        return self.db.scalar(stmt) or 0

    def get_totals_by_type(self, user_id: uuid.UUID) -> Dict[str, Decimal]:
        """Returns dict of {'income': total, 'expense': total}."""
        stmt = (
            select(Transaction.transaction_type, func.sum(Transaction.amount))
            .where(Transaction.user_id == user_id)
            .group_by(Transaction.transaction_type)
        )
        results = self.db.execute(stmt).all()
        totals = {"income": Decimal("0.00"), "expense": Decimal("0.00")}
        for t_type, total in results:
            if t_type in totals:
                totals[t_type] = Decimal(str(total or 0.0))
        return totals

    def get_category_breakdown(self, user_id: uuid.UUID, transaction_type: str = "expense") -> List[Tuple[str, Decimal, int]]:
        """Returns list of (category, total_amount, count) grouped by category."""
        stmt = (
            select(
                Transaction.category,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count")
            )
            .where(Transaction.user_id == user_id, Transaction.transaction_type == transaction_type)
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
        )
        rows = self.db.execute(stmt).all()
        return [(cat, Decimal(str(tot or 0)), cnt) for cat, tot, cnt in rows]

    def get_by_source_reference(
        self,
        user_id: uuid.UUID,
        source_type: str,
        source_reference: str
    ) -> Optional[Transaction]:
        """Finds a transaction by user, source_type and source_reference (e.g. sms_hash)."""
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.source_type == source_type,
            Transaction.source_reference == source_reference
        )
        return self.db.scalars(stmt).first()
