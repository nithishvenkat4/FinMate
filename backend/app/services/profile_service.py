"""Financial Profile domain service."""

import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.models.profile import FinancialProfile
from app.repositories.profile_repo import ProfileRepository
from app.schemas.profile import FinancialProfileCreate, FinancialProfileUpdate


class ProfileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProfileRepository(db)

    def get_or_create(self, user_id: uuid.UUID) -> FinancialProfile:
        profile = self.repo.get_by_user_id(user_id)
        if not profile:
            logger.info("Initializing baseline financial profile for user %s", user_id)
            profile = FinancialProfile(
                user_id=user_id,
                monthly_income=Decimal("60000.00"),
                monthly_fixed_expenses=Decimal("25000.00"),
                current_savings=Decimal("150000.00"),
                risk_preference="moderate"
            )
            profile = self.repo.create(profile)
        return profile

    def update(self, user_id: uuid.UUID, data: FinancialProfileUpdate) -> FinancialProfile:
        profile = self.get_or_create(user_id)
        if data.monthly_income is not None:
            profile.monthly_income = data.monthly_income
        if data.monthly_fixed_expenses is not None:
            profile.monthly_fixed_expenses = data.monthly_fixed_expenses
        if data.current_savings is not None:
            profile.current_savings = data.current_savings
        if data.risk_preference is not None:
            profile.risk_preference = data.risk_preference.lower()

        logger.info("Updated financial profile for user %s", user_id)
        return self.repo.update(profile)
