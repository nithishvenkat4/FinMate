"""Base definitions for future specialized AI financial agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel


class AgentContext(BaseModel):
    user_id: uuid.UUID
    interaction_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    agent_name: str
    insights: str
    deterministic_grounding: Dict[str, Any]
    requires_user_approval: bool = True


class BaseSpecializedAgent(ABC):
    """Abstract interface for all specialized financial agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the specialized agent."""
        pass

    @abstractmethod
    async def analyze(self, context: AgentContext) -> AgentResponse:
        """Analyzes user data and returns explainable, grounded insights."""
        pass
