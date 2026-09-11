from __future__ import annotations

import enum
import json
from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.user import User

SCOPE_DOCUMENT = "document"
SCOPE_SELECTED = "selected"
SCOPE_LIBRARY = "library"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160), default="New conversation", nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default=SCOPE_DOCUMENT, server_default="document", nullable=False)
    document_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="conversations")
    document: Mapped["Document"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def parsed_document_ids(self) -> List[str]:
        if self.scope == SCOPE_LIBRARY:
            return []
        if self.scope == SCOPE_SELECTED and self.document_ids:
            try:
                values = json.loads(self.document_ids)
                if isinstance(values, list):
                    return [str(item) for item in values if item]
            except json.JSONDecodeError:
                pass
        return [self.document_id] if self.document_id else []


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sources: Mapped[List["MessageSource"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
    )


class MessageSource(Base):
    __tablename__ = "message_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    document_chunk_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    message: Mapped[Message] = relationship(back_populates="sources")
