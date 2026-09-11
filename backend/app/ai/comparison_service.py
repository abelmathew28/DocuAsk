from __future__ import annotations

from typing import List, Tuple

from app.ai.citation_service import verify_answer
from app.ai.prompts import insufficient_message, is_insufficient_answer
from app.ai.types import RetrievedChunk
from app.core.exceptions import ValidationAppError
from app.models.document import DocumentStatus

COMPARE_SYSTEM = """You are DocuAsk comparing two documents.

Use ONLY the provided excerpts. Clearly name which document each claim comes from.

Write:

## Overview
## Added in B
## Removed from A
## Modified
## Conflicts
## Unchanged
## Sources

Focus on dates, amounts, requirements, and meaningful wording changes — not a raw text diff.
Cite [Source N] for every major claim.
"""


class ComparisonService:
    def __init__(self, chat) -> None:
        self.chat = chat

    def run(
        self,
        user_id: str,
        document_a_id: str,
        document_b_id: str,
        question: str = "",
    ) -> Tuple[str, List[RetrievedChunk]]:
        docs = []
        for document_id in (document_a_id, document_b_id):
            document = self.chat.documents.get(document_id, user_id)
            if not document or document.status != DocumentStatus.READY.value:
                raise ValidationAppError("Both documents must be indexed before they can be compared.")
            docs.append(document)
        prompt = question.strip() or (
            f"Compare {docs[0].name} (A) with {docs[1].name} (B). "
            "Identify added, removed, modified, and conflicting information."
        )
        chunks_a = self.chat.retrieve(user_id, prompt, [docs[0].id])
        chunks_b = self.chat.retrieve(user_id, prompt, [docs[1].id])
        fused = [*chunks_a[:5], *chunks_b[:5]]
        if not fused:
            return insufficient_message("selected"), []
        labeled = []
        for chunk in fused:
            tag = "A" if chunk.document_id == docs[0].id else "B"
            labeled.append(
                RetrievedChunk(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=f"{tag}: {chunk.document_name}",
                    page_number=chunk.page_number,
                    text=chunk.text,
                    score=chunk.score,
                    heading=chunk.heading,
                    chunk_type=chunk.chunk_type,
                    bbox=chunk.bbox,
                )
            )
        answer = self.chat.complete_from_chunks(
            prompt,
            labeled,
            "selected",
            system=COMPARE_SYSTEM,
            max_tokens=1200,
        )
        if is_insufficient_answer(answer):
            return insufficient_message("selected"), []
        return verify_answer(answer, fused, insufficient_message("selected"))
