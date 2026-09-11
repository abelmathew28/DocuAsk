from __future__ import annotations

from typing import List, Optional

from app.ai.prompts import insufficient_message
from app.models.document import DocumentStatus

SUMMARIZE_SYSTEM = """You are DocuAsk summarizing documents from retrieved excerpts only.
Write a {kind} summary. Cite [Source N] where a claim is specific.
Do not invent facts that are not in the excerpts.
"""


class SummarizationService:
    def __init__(self, chat) -> None:
        self.chat = chat

    def run(
        self,
        user_id: str,
        document_ids: Optional[List[str]],
        kind: str = "quick",
        focus: str = "",
    ) -> tuple[str, list]:
        kind = kind if kind in {"quick", "detailed", "key_points", "section"} else "quick"
        docs = self.chat.documents.list_for_user(user_id, status=DocumentStatus.READY.value)
        if document_ids is not None:
            docs = [item for item in docs if item.id in set(document_ids)]
        if not docs:
            return insufficient_message("document"), []

        question = focus.strip() or {
            "quick": "Summarize the main points of these documents.",
            "detailed": "Write a detailed summary covering each major section.",
            "key_points": "List the key points, dates, and requirements.",
            "section": "Summarize each section separately.",
        }[kind]

        parts = []
        used = []
        for document in docs[:8]:
            chunks = self.chat.retrieve(user_id, question, [document.id])
            used.extend(chunks[:4])
            if not chunks:
                if document.summary:
                    parts.append(f"### {document.name}\n{document.summary}")
                continue
            piece = self.chat.complete_from_chunks(
                f"{question} Focus on {document.name}.",
                chunks[:6],
                "document",
                system=SUMMARIZE_SYSTEM.format(kind=kind.replace("_", " ")),
                max_tokens=700 if kind == "detailed" else 400,
            )
            parts.append(f"### {document.name}\n{piece}")
        if not parts:
            return insufficient_message("document"), []
        return "\n\n".join(parts), used[:8]
