"""Analytics API endpoints."""

from typing import Optional
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.analytics import AnalyticsSummaryResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Calculates and returns deterministic financial metrics and cash flow summary."""
    uid = resolve_user_id(user_id, db)
    service = AnalyticsService(db)
    return service.get_summary(uid)
