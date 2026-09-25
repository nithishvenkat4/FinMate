"""Base Agent Interface for FinMate Specialized Agents (Phase 4)."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.ai.agents.protocol import AgentResult
from app.ai.tools.registry import ToolRegistry, ToolContext

logger = logging.getLogger("finmate.ai.agent")


class BaseAgent(ABC):
    """Abstract base class for all FinMate specialized financial agents."""

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief summary of the agent's purpose and responsibilities."""
        pass

    @property
    @abstractmethod
    def allowed_tools(self) -> List[str]:
        """List of tools this agent is authorized to invoke."""
        pass

    def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: uuid.UUID,
        task_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Invokes a tool via the central ToolRegistry with security context."""
        context = ToolContext(
            user_id=user_id,
            agent_name=self.name,
            task_id=task_id
        )
        return self.tool_registry.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            context=context
        )

    @abstractmethod
    async def process(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        query: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Executes the agent's reasoning, tool calls, and returns structured result."""
        pass
