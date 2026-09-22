"""Financial Profile API endpoints."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.profile import FinancialProfileCreate, FinancialProfileResponse, FinancialProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Financial Profile"])


def get_current_user_id(user_id: Optional[uuid.UUID] = None, db: Session = Depends(get_db)) -> uuid.UUID:
    """Resolves the user context: provided user_id or default demo user."""
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    user = user_repo.get_or_create_default_user()
    return user.id


@router.get("", response_model=FinancialProfileResponse)
def get_profile(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Retrieves financial profile for user."""
    uid = get_current_user_id(user_id, db)
    service = ProfileService(db)
    return service.get_or_create(uid)


@router.post("", response_model=FinancialProfileResponse)
def create_or_update_profile(
    profile_in: FinancialProfileCreate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Initializes or updates financial profile."""
    uid = profile_in.user_id or get_current_user_id(user_id, db)
    service = ProfileService(db)
    update_data = FinancialProfileUpdate(
        monthly_income=profile_in.monthly_income,
        monthly_fixed_expenses=profile_in.monthly_fixed_expenses,
        current_savings=profile_in.current_savings,
        risk_preference=profile_in.risk_preference
    )
    return service.update(uid, update_data)


@router.put("", response_model=FinancialProfileResponse)
def update_profile(
    profile_in: FinancialProfileUpdate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Updates user's financial profile."""
    uid = get_current_user_id(user_id, db)
    service = ProfileService(db)
    return service.update(uid, profile_in)
