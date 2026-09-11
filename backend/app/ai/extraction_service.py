from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple

from app.ai.prompts import insufficient_message
from app.ai.types import RetrievedChunk
from app.models.document import DocumentStatus

EXTRACT_SYSTEM = """You are DocuAsk extracting structured facts from documents.

Return a Markdown table with columns: Field | Value | Document | Page
Only include rows supported by the excerpts.
Use the field names requested by the user.
If nothing is found, say so in one sentence.
"""

FIELD_ALIASES = {
    "people": "people",
    "person": "people",
    "organizations": "organizations",
    "orgs": "organizations",
    "dates": "dates",
    "deadlines": "deadlines",
    "requirements": "requirements",
    "amounts": "amounts",
    "money": "amounts",
    "contacts": "contacts",
    "action items": "action_items",
    "skills": "key_terms",
    "education": "requirements",
    "experience": "requirements",
}


class ExtractionService:
    def __init__(self, chat) -> None:
        self.chat = chat

    def run(
        self,
        user_id: str,
        question: str,
        document_ids: Optional[List[str]],
        history: Optional[list] = None,
    ) -> Tuple[str, List[RetrievedChunk]]:
        chunks = self.chat.retrieve(user_id, question, document_ids, history)
        heuristic = self._heuristic_table(user_id, document_ids, question)
        if not chunks and not heuristic:
            return insufficient_message("selected" if document_ids else "library"), []
        if chunks:
            answer = self.chat.complete_from_chunks(
                question if "extract" in question.lower() else f"Extract: {question}",
                chunks,
                "selected" if document_ids else "library",
                history,
                system=EXTRACT_SYSTEM,
                max_tokens=900,
            )
            if answer and "couldn't find" not in answer.lower():
                return answer, chunks[:6]
        return heuristic or insufficient_message("selected" if document_ids else "library"), chunks[:6]

    def structured(
        self,
        user_id: str,
        document_ids: Optional[List[str]],
        fields: List[str],
    ) -> dict:
        wanted = [FIELD_ALIASES.get(item.lower().strip(), item.lower().strip()) for item in fields] or [
            "dates",
            "deadlines",
            "requirements",
            "contacts",
            "amounts",
        ]
        rows = []
        docs = self._docs(user_id, document_ids)
        for document in docs:
            payload = {}
            if document.intelligence:
                try:
                    payload = json.loads(document.intelligence)
                except json.JSONDecodeError:
                    payload = {}
            for field in wanted:
                for value in payload.get(field, []) if isinstance(payload.get(field), list) else []:
                    rows.append(
                        {
                            "field": field,
                            "value": value,
                            "document_id": document.id,
                            "document": document.name,
                            "page": None,
                            "excerpt": value[:280],
                        }
                    )
        return {"fields": wanted, "rows": rows}

    def _heuristic_table(self, user_id: str, document_ids: Optional[List[str]], question: str) -> str:
        data = self.structured(user_id, document_ids, _fields_from_question(question))
        if not data["rows"]:
            return ""
        lines = ["| Field | Value | Document |", "| --- | --- | --- |"]
        for row in data["rows"][:40]:
            lines.append(f"| {row['field']} | {row['value']} | {row['document']} |")
        return "\n".join(lines)

    def _docs(self, user_id: str, document_ids: Optional[List[str]]):
        ready = self.chat.documents.list_for_user(user_id, status=DocumentStatus.READY.value)
        if document_ids is None:
            return ready
        wanted = set(document_ids)
        return [item for item in ready if item.id in wanted]


def _fields_from_question(question: str) -> List[str]:
    found = []
    lowered = question.lower()
    for alias, field in FIELD_ALIASES.items():
        if alias in lowered and field not in found:
            found.append(field)
    return found
