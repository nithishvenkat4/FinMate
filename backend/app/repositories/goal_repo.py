"""Goal repository module."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.goal import Goal
from app.repositories.base import BaseRepository


class GoalRepository(BaseRepository[Goal]):
    def __init__(self, db: Session):
        super().__init__(Goal, db)

    def get_by_id_and_user(self, id: uuid.UUID, user_id: uuid.UUID) -> Optional[Goal]:
        stmt = select(Goal).where(Goal.id == id, Goal.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_all_by_user(self, user_id: uuid.UUID) -> List[Goal]:
        stmt = select(Goal).where(Goal.user_id == user_id).order_by(Goal.target_date.asc())
        return list(self.db.scalars(stmt).all())

    def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(Goal).where(Goal.user_id == user_id)
        return len(list(self.db.scalars(stmt).all()))
