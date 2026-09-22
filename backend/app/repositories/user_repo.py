"""User repository module."""

from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email.lower().strip())
        return self.db.scalars(stmt).first()

    def get_or_create_default_user(self) -> User:
        """Retrieves or provisions the primary default demo user for Phase 0."""
        user = self.get_by_email("demo@finmate.local")
        if not user:
            user = User(
                name="Aarav Sharma",
                email="demo@finmate.local"
            )
            self.create(user)
        return user
