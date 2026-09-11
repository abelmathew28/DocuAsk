from __future__ import annotations

from typing import List, Optional, Tuple

from app.ai.citation_service import verify_answer
from app.ai.prompts import insufficient_message, is_insufficient_answer
from app.ai.query_service import search_queries
from app.ai.types import RetrievedChunk

RESEARCH_SYSTEM = """You are DocuAsk in Research Mode.

Use ONLY the provided excerpts. Do not invent sources.

Write a structured research brief with these headings:

## Overview
## Common findings
## Differences
## Conflicts
## Sources

Cite every major claim with [Source N] numbers from the excerpts.
If the excerpts do not support a comparison, say so clearly.
If nothing relevant was found, reply with the fallback sentence provided.
"""


class ResearchService:
    def __init__(self, chat) -> None:
        self.chat = chat

    def run(
        self,
        user_id: str,
        question: str,
        document_ids: Optional[List[str]],
        history: Optional[list] = None,
    ) -> Tuple[str, List[RetrievedChunk]]:
        fallback = insufficient_message("library" if document_ids is None else "selected")
        queries = search_queries(question)
        fused: List[RetrievedChunk] = []
        seen = set()
        for query in queries:
            for chunk in self.chat.retrieve(user_id, query, document_ids, history):
                if chunk.id in seen:
                    continue
                seen.add(chunk.id)
                fused.append(chunk)
        fused.sort(key=lambda item: item.score, reverse=True)
        fused = fused[:8]
        if not fused:
            return fallback, []
        answer = self.chat.complete_from_chunks(
            question,
            fused,
            "library" if document_ids is None else "selected",
            history,
            system=RESEARCH_SYSTEM,
            max_tokens=1200,
        )
        if is_insufficient_answer(answer):
            return fallback, []
        return verify_answer(answer, fused, fallback)
