from __future__ import annotations

from typing import List, Optional

from app.ai.hybrid_search import keyword_score
from app.ai.types import RetrievedChunk
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("ai.rerank")


class Reranker:
    def rerank(self, query: str, chunks: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        raise NotImplementedError


class LexicalReranker(Reranker):
    def rerank(self, query: str, chunks: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        if not chunks:
            return []
        for chunk in chunks:
            lexical = keyword_score(query, chunk.text)
            heading_bonus = 0.04 if chunk.heading and keyword_score(query, chunk.heading) > 0.3 else 0.0
            chunk.score = round(0.72 * chunk.score + 0.28 * lexical + heading_bonus, 6)
            if len(chunk.text or "") < 48:
                chunk.score = round(chunk.score * 0.45, 6)
            elif (chunk.chunk_type or "") == "heading" and len(chunk.text or "") < 80:
                chunk.score = round(chunk.score * 0.7, 6)
            head = (chunk.heading or chunk.text[:48]).lower()
            if head.startswith("dear ") or "hiring team" in head:
                chunk.score = round(chunk.score * 0.5, 6)
        chunks.sort(key=lambda item: item.score, reverse=True)
        return chunks[:top_k]


class CrossEncoderReranker(Reranker):
    def __init__(self) -> None:
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        except Exception as exc:
            logger.warning("cross_encoder_unavailable", error=str(exc))
            self._model = False
        return self._model

    def rerank(self, query: str, chunks: List[RetrievedChunk], top_k: int) -> List[RetrievedChunk]:
        model = self._load()
        if not model:
            return LexicalReranker().rerank(query, chunks, top_k)
        pairs = [(query, chunk.text[:1200]) for chunk in chunks]
        try:
            scores = model.predict(pairs)
        except Exception as exc:
            logger.warning("cross_encoder_failed", error=str(exc))
            return LexicalReranker().rerank(query, chunks, top_k)
        for chunk, score in zip(chunks, scores):
            chunk.score = float(score)
        chunks.sort(key=lambda item: item.score, reverse=True)
        return chunks[:top_k]


def get_reranker() -> Reranker:
    choice = (settings.RERANKER or "lexical").lower()
    if choice in {"cross-encoder", "cross_encoder", "ce"}:
        return CrossEncoderReranker()
    return LexicalReranker()
