from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence

from app.ai.types import RetrievedChunk

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "what",
    "how", "many", "does", "do", "should", "this", "that", "with", "from", "your",
    "listed", "listing", "mention", "mentioned", "describe", "described",
    "document", "documents", "information", "info", "please", "file", "files",
    "selected", "there", "here", "any", "some", "also", "into",
}


def tokenize(text: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if token not in _STOP and len(token) > 1]


def keyword_score(query: str, text: str) -> float:
    terms = tokenize(query)
    if not terms:
        return 0.0
    blob = (text or "").lower()
    hits = sum(1 for term in terms if term in blob)
    phrase = query.strip().lower()
    bonus = 0.25 if len(phrase) > 4 and phrase in blob else 0.0
    # Prefer exact identifiers, dates, and codes.
    exact = 0.0
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", blob):
            exact += 0.04 if any(ch.isdigit() for ch in term) or len(term) > 5 else 0.015
    # Expanded search queries can have many synonyms; do not dilute a real hit.
    denom = min(max(len(terms), 1), 6)
    return min(1.0, hits / denom + bonus + exact)


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[RetrievedChunk]],
    k: int = 60,
) -> List[RetrievedChunk]:
    scores: Dict[str, float] = {}
    items: Dict[str, RetrievedChunk] = {}
    for ranked in ranked_lists:
        for rank, chunk in enumerate(ranked, start=1):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
            if chunk.id not in items:
                items[chunk.id] = chunk
            else:
                items[chunk.id].score = max(items[chunk.id].score, chunk.score)
    fused = []
    for chunk_id, rrf in scores.items():
        chunk = items[chunk_id]
        chunk.score = round(0.65 * chunk.score + 0.35 * rrf * 10, 6)
        fused.append(chunk)
    fused.sort(key=lambda item: item.score, reverse=True)
    return fused
