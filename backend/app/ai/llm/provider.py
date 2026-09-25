"""LLM Provider Abstraction Layer for FinMate.

Providers:
- MockLLMProvider: 100% deterministic, offline, zero external cost, safe for testing.
- OpenAILLMProvider: Invokes OpenAI chat completions when configured.
- GeminiLLMProvider: Invokes Google Gemini generateContent API when configured.

Architectural Rule:
The LLM never computes authoritative arithmetic. All numbers come from backend services.
"""

from abc import ABC, abstractmethod
import json
import logging
from typing import Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("finmate.ai.llm")

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract interface for natural language reasoning and explanation providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_message: str = "") -> str:
        """Generates plain text reasoning."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_message: str,
        schema: Type[T]
    ) -> T:
        """Generates structured output validated against a Pydantic schema."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock LLM Provider for offline development and test automation."""

    def __init__(self, model_name: str = "mock-reasoner-v1"):
        self.model_name = model_name

    async def generate(self, prompt: str, system_message: str = "") -> str:
        return (
            f"[MOCK LLM RESPONSE ({self.model_name})]: "
            "Based on your calculated surplus and active financial goals, "
            "your current cashflow demonstrates healthy stability."
        )

    async def generate_structured(
        self,
        prompt: str,
        system_message: str,
        schema: Type[T]
    ) -> T:
        # Synthesize deterministic structured response from prompt context
        # Extract potential query
        summary_text = (
            "FinMate deterministic analysis confirms that your monthly surplus can accommodate "
            "planned commitments, provided emergency reserves remain untouched."
        )
        if "laptop" in prompt.lower():
            summary_text = (
                "You have an estimated monthly surplus of ₹25,000 against monthly fixed commitments of ₹15,000. "
                "Purchasing a ₹20,000 laptop is feasible using single-month cashflow surplus, but it consumes "
                "80% of your disposable surplus for that month. Ensure your ₹1,20,000 emergency fund is not depleted."
            )

        data = {
            "summary": summary_text,
            "key_factors": [
                "Monthly income stability (₹60,000)",
                "Active High Priority Goal: Higher Education (₹3,00,000 target)",
                "Sufficient liquid savings for baseline emergency reserves"
            ],
            "evidence_used": [
                "FPSB India 50/30/20 Discretionary Outlay Guideline",
                "RBI Financial Education Contingency Fund Recommendations"
            ],
            "uncertainties": [
                "Discretionary utility and food spending may vary by ±10%",
                "Seasonal expenses in upcoming quarter could reduce liquid margin"
            ],
            "action_options": [
                "Option 1: Purchase outright from current month's ₹25,000 surplus without touching emergency funds.",
                "Option 2: Apply the 30-Day Waiting Rule to ensure purchase remains essential.",
                "Option 3: Split outlay across two monthly cycles to maintain goal savings rate."
            ],
            "user_decision_required": True,
            "provider": f"mock ({self.model_name})"
        }
        return schema.model_validate(data)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API integration for production natural language explanations."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name

    async def generate(self, prompt: str, system_message: str = "") -> str:
        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_message or "You are FinMate financial assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def generate_structured(
        self,
        prompt: str,
        system_message: str,
        schema: Type[T]
    ) -> T:
        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        json_prompt = (
            f"{prompt}\n\nReturn your answer strictly in valid JSON matching this schema: "
            f"{json.dumps(schema.model_json_schema())}"
        )
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": json_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            res_json = json.loads(resp.json()["choices"][0]["message"]["content"])
            return schema.model_validate(res_json)


def get_llm_provider(override_provider: Optional[str] = None) -> BaseLLMProvider:
    """Factory creating appropriate LLM provider based on settings."""
    provider_type = override_provider or getattr(settings, "LLM_PROVIDER", "mock") or "mock"
    provider_type = provider_type.lower().strip()

    if provider_type == "openai" and getattr(settings, "LLM_API_KEY", ""):
        return OpenAILLMProvider(
            api_key=settings.LLM_API_KEY,
            model_name=getattr(settings, "LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini"
        )
    # Default to robust, zero-cost mock provider
    return MockLLMProvider()
