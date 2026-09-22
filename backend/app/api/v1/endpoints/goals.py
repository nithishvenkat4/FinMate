"""Financial Goals API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.common import MessageResponse
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goals"])


def resolve_user_id(user_id: Optional[uuid.UUID], db: Session) -> uuid.UUID:
    if user_id:
        return user_id
    user_repo = UserRepository(db)
    return user_repo.get_or_create_default_user().id


@router.get("", response_model=List[GoalResponse])
def get_goals(
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Lists all financial goals with calculated progress percentage."""
    uid = resolve_user_id(user_id, db)
    service = GoalService(db)
    return service.list(uid)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_in: GoalCreate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Creates a new financial goal."""
    uid = goal_in.user_id or resolve_user_id(user_id, db)
    service = GoalService(db)
    return service.create(uid, goal_in)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Retrieves a single goal by ID."""
    uid = resolve_user_id(user_id, db)
    service = GoalService(db)
    return service.get_by_id(goal_id, uid)


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: uuid.UUID,
    goal_in: GoalUpdate,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Updates a financial goal."""
    uid = resolve_user_id(user_id, db)
    service = GoalService(db)
    return service.update(goal_id, uid, goal_in)


@router.delete("/{goal_id}", response_model=MessageResponse)
def delete_goal(
    goal_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """Deletes a financial goal."""
    uid = resolve_user_id(user_id, db)
    service = GoalService(db)
    service.delete(goal_id, uid)
    return MessageResponse(message="Goal successfully deleted")
