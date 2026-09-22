"""LLM Provider abstraction placeholder (Phase 7)."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseLLMProvider(ABC):
    """Abstract interface for natural-language reasoning providers."""

    @abstractmethod
    async def generate_explanation(self, prompt: str, context: Dict[str, Any]) -> str:
        """Explains deterministic financial outputs in natural language."""
        pass
