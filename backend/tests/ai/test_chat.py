from __future__ import annotations

from typing import List, Sequence

from app.ai.chat import ChatService, INSUFFICIENT_ANSWER
from app.ai.provider import AIProvider
from app.ai.types import RetrievedChunk
from app.models.conversation import Conversation
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.user import User
from app.core.security import hash_password


class FakeProvider(AIProvider):
    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [[float(len(text)), 1.0, 0.0] for text in texts]

    def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
        self.calls += 1
        return "Employees receive 15 vacation days. [invented]"


def test_chat_returns_insufficient_without_chunks(db):
    user = User(name="Abel", email="abel@example.com", password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    document = Document(
        user_id=user.id,
        name="Handbook",
        original_filename="handbook.pdf",
        storage_path="x.pdf",
        file_size=10,
        status=DocumentStatus.READY.value,
        page_count=1,
    )
    db.add(document)
    db.commit()
    conversation = Conversation(user_id=user.id, document_id=document.id, title="New conversation")
    db.add(conversation)
    db.commit()

    service = ChatService(db, provider=FakeProvider())
    _, assistant = service.ask(conversation, document, "What is the vacation policy?")
    assert INSUFFICIENT_ANSWER in assistant.content
    assert assistant.sources == []


def test_chat_attaches_real_sources(db):
    user = User(name="Abel", email="abel2@example.com", password_hash=hash_password("password123"))
    db.add(user)
    db.commit()
    document = Document(
        user_id=user.id,
        name="Employee-Handbook.pdf",
        original_filename="Employee-Handbook.pdf",
        storage_path="x.pdf",
        file_size=10,
        status=DocumentStatus.READY.value,
        page_count=1,
    )
    db.add(document)
    db.commit()
    db.add(
        DocumentChunk(
            document_id=document.id,
            user_id=user.id,
            page_number=14,
            chunk_index=0,
            text="Vacation policy: full-time employees receive 15 paid vacation days each year.",
            embedding=[40.0, 1.0, 0.0],
        )
    )
    db.commit()
    conversation = Conversation(user_id=user.id, document_id=document.id, title="New conversation")
    db.add(conversation)
    db.commit()

    provider = FakeProvider()
    service = ChatService(db, provider=provider)

    def fake_complete(system_prompt, messages, max_tokens):
        return "Full-time employees receive 15 paid vacation days each year."

    provider.complete = fake_complete  # type: ignore[method-assign]
    _, assistant = service.ask(conversation, document, "What is the vacation policy?")
    assert assistant.sources
    assert assistant.sources[0].page_number == 14
    assert assistant.sources[0].document_name == "Employee-Handbook.pdf"
    assert assistant.sources[0].document_id == document.id
    assert "15" in assistant.content


def test_complete_from_chunks_quotes_experience_when_llm_gives_up(db):
    class InsufficientProvider(AIProvider):
        def embed(self, texts: Sequence[str]) -> List[List[float]]:
            return [[float(len(text)), 1.0, 0.0] for text in texts]

        def complete(self, system_prompt: str, messages: List[dict], max_tokens: int) -> str:
            return INSUFFICIENT_ANSWER

    service = ChatService(db, provider=InsufficientProvider())
    chunks = [
        RetrievedChunk(
            id="1",
            document_id="d",
            document_name="Resume.pdf",
            page_number=1,
            text=(
                "Full Stack Developer | UI/UX Designer  August 2024 - Present\n"
                "Company: RDAlabs\n"
                "Designed and developed Invoice Gen, a billing platform used by operations teams."
            ),
            score=0.82,
            heading="PROFESSIONAL EXPERIENCE",
        )
    ]
    answer = service.complete_from_chunks("What experience is listed?", chunks, "document")
    assert INSUFFICIENT_ANSWER not in answer
    assert "rdalabs" in answer.lower() or "invoice gen" in answer.lower()
