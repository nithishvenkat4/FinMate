"""Financial Goal domain service."""

from typing import List
import uuid
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundException
from app.core.logging import logger
from app.models.goal import Goal
from app.repositories.goal_repo import GoalRepository
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.calculations import calculate_goal_progress


class GoalService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GoalRepository(db)

    def _to_response(self, goal: Goal) -> GoalResponse:
        progress = calculate_goal_progress(goal.current_amount, goal.target_amount)
        return GoalResponse(
            id=goal.id,
            user_id=goal.user_id,
            name=goal.name,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=goal.target_date,
            priority=goal.priority,
            progress_percentage=progress,
            created_at=goal.created_at,
            updated_at=goal.updated_at
        )

    def create(self, user_id: uuid.UUID, data: GoalCreate) -> GoalResponse:
        logger.info("Creating goal '%s' for user %s (target: %s)", data.name, user_id, data.target_amount)
        goal = Goal(
            user_id=user_id,
            name=data.name.strip(),
            target_amount=data.target_amount,
            current_amount=data.current_amount,
            target_date=data.target_date,
            priority=data.priority.lower()
        )
        saved = self.repo.create(goal)
        return self._to_response(saved)

    def get_by_id(self, id: uuid.UUID, user_id: uuid.UUID) -> GoalResponse:
        goal = self.repo.get_by_id_and_user(id, user_id)
        if not goal:
            raise EntityNotFoundException("Goal", id)
        return self._to_response(goal)

    def list(self, user_id: uuid.UUID) -> List[GoalResponse]:
        goals = self.repo.get_all_by_user(user_id)
        return [self._to_response(g) for g in goals]

    def update(self, id: uuid.UUID, user_id: uuid.UUID, data: GoalUpdate) -> GoalResponse:
        goal = self.repo.get_by_id_and_user(id, user_id)
        if not goal:
            raise EntityNotFoundException("Goal", id)

        if data.name is not None:
            goal.name = data.name.strip()
        if data.target_amount is not None:
            goal.target_amount = data.target_amount
        if data.current_amount is not None:
            goal.current_amount = data.current_amount
        if data.target_date is not None:
            goal.target_date = data.target_date
        if data.priority is not None:
            goal.priority = data.priority.lower()

        saved = self.repo.update(goal)
        logger.info("Updated goal %s for user %s", id, user_id)
        return self._to_response(saved)

    def delete(self, id: uuid.UUID, user_id: uuid.UUID) -> None:
        goal = self.repo.get_by_id_and_user(id, user_id)
        if not goal:
            raise EntityNotFoundException("Goal", id)
        self.repo.delete(goal)
        logger.info("Deleted goal %s for user %s", id, user_id)
