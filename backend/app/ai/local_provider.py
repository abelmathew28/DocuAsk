from __future__ import annotations

import hashlib
import math
import re
from typing import List, Sequence

from app.ai.provider import AIProvider
from app.ai.list_answer import format_list_answer
from app.ai.query_service import expanded_terms, term_overlap
from app.ai.types import RetrievedChunk
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.core.logging import get_logger

logger = get_logger("ai.local")

_local_model = None


class HashEmbeddingProvider(AIProvider):
    """Deterministic local embeddings for tests and fallback when transformers are unavailable."""

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        dim = settings.embedding_dimensions
        vectors: List[List[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            values = []
            seed = digest
            while len(values) < dim:
                for byte in seed:
                    values.append((byte / 127.5) - 1.0)
                    if len(values) >= dim:
                        break
                seed = hashlib.sha256(seed).digest()
            norm = math.sqrt(sum(v * v for v in values)) or 1.0
            vectors.append([v / norm for v in values])
        return vectors

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        raise ProviderError("This embedding backend does not generate answers.")


class LocalEmbeddingProvider(AIProvider):
    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        model = _load_sentence_model()
        if model is None:
            logger.warning("sentence_transformers_missing_using_hash")
            return HashEmbeddingProvider().embed(texts)
        vectors = model.encode(list(texts), normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        raise ProviderError("The local embedding backend does not generate answers.")


_INSUFFICIENT = "I could not find enough information in the selected documents to answer this."
_COVER_MARKERS = ("dear hiring", "dear sir", "to whom it may concern", "i am writing", "i am excited to apply")


def extract_from_passages(question: str, passages: Sequence[str], fallback: str | None = None) -> str:
    """Quote or list the retrieved passages that match the question."""
    insufficient = fallback or _INSUFFICIENT
    listing = _is_listing_question(question)
    if listing:
        chunks = [
            RetrievedChunk(
                id=str(index),
                document_id="passage",
                document_name="",
                page_number=1,
                text=passage,
                score=1.0,
                heading=None,
                chunk_index=index,
            )
            for index, passage in enumerate(passages)
        ]
        return format_list_answer(question, chunks, insufficient)
    terms = expanded_terms(question)
    scored: List[tuple[float, str]] = []
    for passage in passages:
        clean = re.sub(r"\s+", " ", (passage or "")).strip()
        if len(clean) < 20 or clean.lower().startswith("question:"):
            continue
        overlap = term_overlap(terms, clean)
        if overlap < 1:
            continue
        score = overlap * 3 + min(len(clean), 280) / 800 + _passage_bonus(question, clean)
        if score <= 0:
            continue
        scored.append((score, clean))
    scored.sort(key=lambda item: item[0], reverse=True)
    picked: List[str] = []
    for _, text in scored:
        snippet = text if len(text) <= 700 else text[:680].rsplit(" ", 1)[0] + "…"
        if snippet not in picked:
            picked.append(snippet)
        if len(picked) == 3:
            break
    if not picked:
        return insufficient
    return "\n\n".join(picked)


def _is_listing_question(question: str) -> bool:
    lowered = (question or "").lower()
    return any(token in lowered for token in ("listed", "list the", "list all", "what are the"))


def _passage_bonus(question: str, text: str) -> float:
    lowered = text.lower()
    head = lowered[:240]
    bonus = 0.0
    if any(marker in head for marker in _COVER_MARKERS) or lowered.startswith("dear "):
        bonus -= 5.0
    return bonus


class ExtractiveProvider(AIProvider):
    """Answer from retrieved passages without a cloud or local LLM."""

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return HashEmbeddingProvider().embed(texts)

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        user = next((item["content"] for item in reversed(messages) if item.get("role") == "user"), "")
        blocks = re.findall(r"\[Source \d+\][^\n]*\n(.+?)(?=\n\[Source |\n\nQuestion:|\Z)", user, flags=re.S)
        question = user
        if "Question:" in user:
            question = user.split("Question:")[-1].split("If the excerpts")[0].strip()
        return extract_from_passages(question, blocks)


class OllamaChatProvider(AIProvider):
    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        raise ProviderError("Ollama is configured for answers, not embeddings.")

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        import httpx

        user = next((item["content"] for item in reversed(messages) if item.get("role") == "user"), "")
        prompt = f"{system_prompt}\n\n{user}"
        try:
            response = httpx.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=120,
            )
            response.raise_for_status()
            return (response.json().get("response") or "").strip()
        except Exception as exc:
            logger.error("ollama_failed", error=str(exc))
            raise ProviderError(
                "Ollama is not reachable. Start Ollama or set LLM_PROVIDER=extractive / openai."
            ) from exc


def _load_sentence_model():
    global _local_model
    if _local_model is False:
        return None
    if _local_model is not None:
        return _local_model
    try:
        from sentence_transformers import SentenceTransformer

        logger.info("loading_local_embeddings", model=settings.EMBEDDING_MODEL)
        _local_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return _local_model
    except Exception as exc:
        logger.warning("local_embeddings_unavailable", error=str(exc))
        _local_model = False
        return None
