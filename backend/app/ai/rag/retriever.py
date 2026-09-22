"""RAG Knowledge Base retriever abstraction placeholder (Phase 6)."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseKnowledgeRetriever(ABC):
    """Abstract interface for retrieving verified financial guidelines."""

    @abstractmethod
    async def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves verified financial domain knowledge."""
        pass
