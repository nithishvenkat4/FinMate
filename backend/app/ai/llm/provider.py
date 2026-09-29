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


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API integration for natural language explanations & decision support."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-1.5-flash",
        base_url: Optional[str] = None
    ):
        self.api_key = api_key
        self.model_name = model_name or "gemini-1.5-flash"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com").rstrip("/")

    async def generate(self, prompt: str, system_message: str = "") -> str:
        import httpx
        url = f"{self.base_url}/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        if system_message:
            payload["systemInstruction"] = {
                "parts": [{"text": system_message}]
            }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            logger.error("Unexpected Gemini response structure: %s", data)
            raise ValueError(f"Gemini API returned malformed response: {err}") from err

    async def generate_structured(
        self,
        prompt: str,
        system_message: str,
        schema: Type[T]
    ) -> T:
        import httpx
        import re
        url = f"{self.base_url}/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        schema_json = json.dumps(schema.model_json_schema())
        json_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: Return your response strictly as valid JSON matching this schema:\n"
            f"{schema_json}\n"
            f"Do not wrap output in markdown code fences, backticks, or comments."
        )

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }
        if system_message:
            payload["systemInstruction"] = {
                "parts": [{"text": system_message}]
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            logger.error("Unexpected Gemini response structure: %s", data)
            raise ValueError(f"Gemini API returned malformed response: {err}") from err

        clean_text = raw_text.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)

        res_json = json.loads(clean_text)
        if hasattr(schema, "model_fields") and "provider" in schema.model_fields:
            if not res_json.get("provider"):
                res_json["provider"] = f"gemini ({self.model_name})"
        return schema.model_validate(res_json)


class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API integration for production natural language explanations."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini",
        base_url: Optional[str] = None
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = (base_url or getattr(settings, "LLM_BASE_URL", "") or "https://api.openai.com/v1").rstrip("/")

    async def generate(self, prompt: str, system_message: str = "") -> str:
        import httpx
        url = f"{self.base_url}/chat/completions"
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
        url = f"{self.base_url}/chat/completions"
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
            if hasattr(schema, "model_fields") and "provider" in schema.model_fields:
                if not res_json.get("provider"):
                    res_json["provider"] = f"openai ({self.model_name})"
            return schema.model_validate(res_json)


def get_llm_provider(override_provider: Optional[str] = None) -> BaseLLMProvider:
    """Factory creating appropriate LLM provider based on settings."""
    provider_type = (override_provider or getattr(settings, "LLM_PROVIDER", "mock") or "mock").lower().strip()
    api_key = getattr(settings, "LLM_API_KEY", "") or getattr(settings, "GEMINI_API_KEY", "")

    # Auto-detect Gemini if provider is gemini, model has gemini, or key starts with AIza
    is_gemini = (
        provider_type == "gemini" or
        "gemini" in getattr(settings, "LLM_MODEL", "").lower() or
        (api_key.startswith("AIza") and provider_type != "openai")
    )

    if (provider_type == "gemini" or is_gemini) and api_key:
        model_name = getattr(settings, "LLM_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash"
        if not model_name.startswith("gemini"):
            model_name = "gemini-1.5-flash"
        return GeminiLLMProvider(
            api_key=api_key,
            model_name=model_name,
            base_url=getattr(settings, "LLM_BASE_URL", None) or None
        )

    if provider_type == "openai" and api_key:
        return OpenAILLMProvider(
            api_key=api_key,
            model_name=getattr(settings, "LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            base_url=getattr(settings, "LLM_BASE_URL", None) or None
        )

    # Default to robust, zero-cost mock provider
    return MockLLMProvider()
