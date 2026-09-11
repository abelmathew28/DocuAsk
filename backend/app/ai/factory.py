from __future__ import annotations

from typing import List, Sequence

from app.ai.local_provider import (
    ExtractiveProvider,
    HashEmbeddingProvider,
    LocalEmbeddingProvider,
    OllamaChatProvider,
)
from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.factory")


class CompositeProvider(AIProvider):
    def __init__(self, embedder: AIProvider, llm: AIProvider) -> None:
        self.embedder = embedder
        self.llm = llm

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return self.embedder.embed(texts)

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        return self.llm.complete(system_prompt, messages, max_tokens)


def _embedder() -> AIProvider:
    choice = settings.EMBEDDING_PROVIDER.lower().strip()
    if choice == "openai":
        if not settings.OPENAI_API_KEY:
            logger.warning("openai_embeddings_missing_key_using_local")
            return LocalEmbeddingProvider()
        return OpenAIProvider()
    if choice == "hash":
        return HashEmbeddingProvider()
    return LocalEmbeddingProvider()


def _llm() -> AIProvider:
    choice = settings.LLM_PROVIDER.lower().strip()
    if choice == "extractive":
        return ExtractiveProvider()
    if choice == "ollama":
        return OllamaChatProvider()
    if choice == "openai":
        if settings.OPENAI_API_KEY:
            return OpenAIProvider()
        logger.warning("openai_chat_missing_key_using_extractive")
        return ExtractiveProvider()
    # auto: try OpenAI when a key exists, but skip if prior requests exhausted quota
    if settings.OPENAI_API_KEY:
        from app.ai.openai_provider import _openai_chat_exhausted

        if _openai_chat_exhausted:
            return ExtractiveProvider()
        return OpenAIProvider()
    return ExtractiveProvider()


def get_ai_provider() -> AIProvider:
    embedder = _embedder()
    llm = _llm()
    logger.debug(
        "ai_backends",
        embeddings=embedder.__class__.__name__,
        llm=llm.__class__.__name__,
    )
    if embedder is llm:
        return embedder
    return CompositeProvider(embedder, llm)
