"""Investment repository module."""

from decimal import Decimal
from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.investment import Investment
from app.repositories.base import BaseRepository


class InvestmentRepository(BaseRepository[Investment]):
    def __init__(self, db: Session):
        super().__init__(Investment, db)

    def get_by_id_and_user(self, id: uuid.UUID, user_id: uuid.UUID) -> Optional[Investment]:
        stmt = select(Investment).where(Investment.id == id, Investment.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_all_by_user(self, user_id: uuid.UUID) -> List[Investment]:
        stmt = select(Investment).where(Investment.user_id == user_id).order_by(Investment.current_value.desc())
        return list(self.db.scalars(stmt).all())

    def get_total_value(self, user_id: uuid.UUID) -> Decimal:
        stmt = select(func.sum(Investment.current_value)).where(Investment.user_id == user_id)
        val = self.db.scalar(stmt)
        return Decimal(str(val or "0.00"))
