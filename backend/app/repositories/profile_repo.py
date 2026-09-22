"""Financial Profile repository module."""

from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.profile import FinancialProfile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[FinancialProfile]):
    def __init__(self, db: Session):
        super().__init__(FinancialProfile, db)

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[FinancialProfile]:
        stmt = select(FinancialProfile).where(FinancialProfile.user_id == user_id)
        return self.db.scalars(stmt).first()
