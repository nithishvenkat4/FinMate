"""Decision and Scenario repository module."""

from typing import List, Optional
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.decision import Decision, Scenario
from app.repositories.base import BaseRepository
from app.schemas.decision import DecisionSimulationResponse


class DecisionRepository(BaseRepository[Decision]):
    def __init__(self, db: Session):
        super().__init__(Decision, db)

    def get_by_id_and_user(self, id: uuid.UUID, user_id: uuid.UUID) -> Optional[Decision]:
        stmt = (
            select(Decision)
            .where(Decision.id == id, Decision.user_id == user_id)
            .options(selectinload(Decision.scenarios))
        )
        return self.db.scalars(stmt).first()

    def get_all_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[Decision]:
        stmt = (
            select(Decision)
            .where(Decision.user_id == user_id)
            .options(selectinload(Decision.scenarios))
            .order_by(Decision.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Decision.id)).where(Decision.user_id == user_id)
        return self.db.scalar(stmt) or 0

    def save_simulation(
        self, user_id: uuid.UUID, sim: DecisionSimulationResponse
    ) -> Decision:
        """Persists a simulated decision and its generated scenarios for future retrieval."""
        dec_info = sim.decision
        decision = Decision(
            user_id=user_id,
            decision_type=dec_info.get("decision_type", "purchase"),
            title=dec_info.get("title", "Financial Decision Simulation"),
            description=dec_info.get("description"),
            amount=dec_info.get("amount"),
            category=dec_info.get("category"),
            status="simulated",
            metadata_json={
                "explanation": sim.explanation.model_dump() if hasattr(sim.explanation, "model_dump") else sim.explanation,
                "baseline": sim.baseline.model_dump(mode="json") if hasattr(sim.baseline, "model_dump") else sim.baseline,
                "assumptions": sim.assumptions,
                "warnings": sim.warnings,
            },
        )
        self.db.add(decision)
        self.db.flush()

        for s in sim.scenarios:
            scenario = Scenario(
                decision_id=decision.id,
                name=s.name,
                description=s.description,
                assumptions=s.assumptions,
                financial_impact=s.financial_impact.model_dump(mode="json") if hasattr(s.financial_impact, "model_dump") else s.financial_impact,
                goal_impact=[g.model_dump(mode="json") for g in s.goal_impact] if hasattr(s.goal_impact[0] if s.goal_impact else None, "model_dump") else s.goal_impact,
                savings_impact=s.savings_impact,
                cash_flow_impact=s.cash_flow_impact,
                timeline_impact=s.timeline_impact,
                warnings=s.warnings,
            )
            self.db.add(scenario)

        self.db.commit()
        self.db.refresh(decision)
        return decision

    def delete_by_id_and_user(self, id: uuid.UUID, user_id: uuid.UUID) -> bool:
        decision = self.get_by_id_and_user(id, user_id)
        if not decision:
            return False
        self.db.delete(decision)
        self.db.commit()
        return True
