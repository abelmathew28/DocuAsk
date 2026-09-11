from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation, Message
from app.models.document import Document


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        return self.db.scalar(
            select(Conversation)
            .options(selectinload(Conversation.messages).selectinload(Message.sources), selectinload(Conversation.document))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )

    def list_for_user(
        self,
        user_id: str,
        document_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages), selectinload(Conversation.document))
            .where(Conversation.user_id == user_id)
        )
        if scope:
            stmt = stmt.where(Conversation.scope == scope)
        if document_id and (scope or "document") == "document":
            stmt = stmt.where(Conversation.document_id == document_id, Conversation.scope == "document")
        stmt = stmt.order_by(Conversation.updated_at.desc())
        return list(self.db.scalars(stmt).all())

    def create(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def save(self, conversation: Conversation) -> Conversation:
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete(self, conversation: Conversation) -> None:
        self.db.delete(conversation)
        self.db.commit()

    def delete_all_for_user(self, user_id: str) -> int:
        conversations = self.list_for_user(user_id)
        count = len(conversations)
        for conversation in conversations:
            self.db.delete(conversation)
        self.db.commit()
        return count

    def count_for_user(self, user_id: str) -> int:
        return self.db.scalar(
            select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
        ) or 0

    def add_message(self, message: Message) -> Message:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_message(self, message_id: str, user_id: str) -> Optional[Message]:
        return self.db.scalar(
            select(Message)
            .join(Conversation)
            .options(selectinload(Message.sources))
            .where(Message.id == message_id, Conversation.user_id == user_id)
        )


def conversation_preview(conversation: Conversation) -> Optional[str]:
    if not conversation.messages:
        return None
    last = conversation.messages[-1]
    text = last.content.strip()
    return text[:140] + ("…" if len(text) > 140 else "")


def to_conversation_public(conversation: Conversation):
    from app.schemas.conversation import ConversationPublic

    document_name = conversation.document.name if conversation.document else None
    return ConversationPublic(
        id=conversation.id,
        document_id=conversation.document_id,
        document_name=document_name,
        title=conversation.title,
        preview=conversation_preview(conversation),
        scope=conversation.scope or "document",
        document_ids=conversation.parsed_document_ids(),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )
