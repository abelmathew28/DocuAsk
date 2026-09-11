from __future__ import annotations

from typing import List, Sequence

from openai import OpenAI

from app.ai.provider import AIProvider
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.core.logging import get_logger

logger = get_logger("ai.openai")
_openai_chat_exhausted = False


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ProviderError(
                "OpenAI is selected, but OPENAI_API_KEY is empty. Add a key, or use local embeddings and extractive/Ollama answers."
            )
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY, max_retries=0, timeout=12.0)
        self.chat_model = settings.OPENAI_CHAT_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=list(texts),
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.error("embedding_failed", error=str(exc))
            raise ProviderError("Failed to generate embeddings. Please try again.") from exc

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        global _openai_chat_exhausted
        if _openai_chat_exhausted:
            raise ProviderError("The OpenAI key is rate-limited or out of quota. Falling back to document excerpts.")
        payload = [{"role": "system", "content": system_prompt}, *messages]
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=payload,
                max_tokens=max_tokens,
                temperature=0.1,
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception as exc:
            logger.error("completion_failed", error=str(exc))
            if "429" in str(exc) or "quota" in str(exc).lower() or "rate" in str(exc).lower():
                _openai_chat_exhausted = True
                raise ProviderError("The OpenAI key is rate-limited or out of quota. Falling back to document excerpts.") from exc
            raise ProviderError("The AI service is unavailable right now. Please try again.") from exc


def get_ai_provider() -> AIProvider:
    from app.ai.factory import get_ai_provider as factory_provider

    return factory_provider()
