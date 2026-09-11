from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy.orm import Session

from app.ai.chat import ChatService
from app.ai.citation_service import compute_support_status
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.models.conversation import (
    SCOPE_DOCUMENT,
    SCOPE_LIBRARY,
    SCOPE_SELECTED,
    Conversation,
    Message,
    MessageRole,
)
from app.models.document import DocumentStatus
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository, to_conversation_public
from app.repositories.document_repository import DocumentRepository
from app.schemas.conversation import (
    ChatResponse,
    ConversationDetail,
    ConversationPublic,
    MessagePublic,
    SourcePublic,
)


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.documents = DocumentRepository(db)
        self.chat = ChatService(db)

    def list(
        self,
        user: User,
        document_id: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> List[ConversationPublic]:
        items = self.conversations.list_for_user(user.id, document_id, scope)
        return [to_conversation_public(item) for item in items]

    def get(self, user: User, conversation_id: str) -> Conversation:
        conversation = self.conversations.get(conversation_id, user.id)
        if not conversation:
            raise NotFoundError("Conversation not found.")
        return conversation

    def create(
        self,
        user: User,
        document_id: Optional[str] = None,
        title: Optional[str] = None,
        scope: str = SCOPE_DOCUMENT,
        document_ids: Optional[List[str]] = None,
    ) -> Conversation:
        scope = scope or SCOPE_DOCUMENT
        ready = [
            item for item in self.documents.list_for_user(user.id, status=DocumentStatus.READY.value)
        ]
        if scope == SCOPE_LIBRARY:
            if not ready:
                raise ValidationAppError("Upload and index a document before asking your whole library.")
            anchor = ready[0]
            conversation = Conversation(
                user_id=user.id,
                document_id=anchor.id,
                title=title or "Library search",
                scope=SCOPE_LIBRARY,
                document_ids=None,
            )
            return self.conversations.create(conversation)

        ids = list(dict.fromkeys(document_ids or ([] if not document_id else [document_id])))
        if scope == SCOPE_SELECTED:
            if len(ids) < 1:
                raise ValidationAppError("Select at least one document.")
        elif not document_id:
            raise ValidationAppError("Choose a document to ask.")
        else:
            ids = [document_id]

        owned = []
        for item_id in ids:
            document = self.documents.get(item_id, user.id)
            if not document:
                raise NotFoundError("Document not found.")
            owned.append(document)
        conversation = Conversation(
            user_id=user.id,
            document_id=owned[0].id,
            title=title or ("Selected files" if scope == SCOPE_SELECTED else "New conversation"),
            scope=scope,
            document_ids=json.dumps([item.id for item in owned]) if scope == SCOPE_SELECTED else None,
        )
        return self.conversations.create(conversation)

    def rename(self, user: User, conversation_id: str, title: str) -> Conversation:
        conversation = self.get(user, conversation_id)
        conversation.title = title.strip()
        return self.conversations.save(conversation)

    def delete(self, user: User, conversation_id: str) -> None:
        conversation = self.get(user, conversation_id)
        self.conversations.delete(conversation)

    def delete_all(self, user: User) -> int:
        return self.conversations.delete_all_for_user(user.id)

    def ask(self, user: User, conversation_id: str, question: str, mode: str = "ask") -> ChatResponse:
        conversation = self.get(user, conversation_id)
        user_message, assistant_message = self.chat.ask(
            conversation, conversation.document, question, mode=mode
        )
        return _to_chat_response(user_message, assistant_message)

    def regenerate(self, user: User, conversation_id: str) -> ChatResponse:
        conversation = self.get(user, conversation_id)
        result = self.chat.regenerate(conversation, conversation.document)
        if not result:
            raise AppError("Unable to regenerate this answer.")
        return _to_chat_response(*result)

    def feedback(self, user: User, message_id: str, rating: str) -> Message:
        message = self.conversations.get_message(message_id, user.id)
        if not message or message.role != MessageRole.ASSISTANT.value:
            raise NotFoundError("Message not found.")
        message.feedback = rating
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def detail(self, conversation: Conversation) -> ConversationDetail:
        public = to_conversation_public(conversation)
        return ConversationDetail(
            **public.model_dump(),
            messages=[_to_message_public(message) for message in conversation.messages],
        )


def _to_message_public(message: Message) -> MessagePublic:
    sources = [
        SourcePublic(
            document=source.document_name,
            page=source.page_number,
            excerpt=source.excerpt,
            relevance_score=source.relevance_score,
            chunk_id=source.document_chunk_id,
            document_id=source.document_id,
        )
        for source in (message.sources or [])
    ]
    support = None
    if message.role == MessageRole.ASSISTANT.value:
        support = compute_support_status(message.content, sources)
    return MessagePublic(
        id=message.id,
        role=message.role,
        content=message.content,
        feedback=message.feedback,
        created_at=message.created_at,
        sources=sources,
        support_status=support,
    )


def _to_chat_response(user_message: Message, assistant_message: Message) -> ChatResponse:
    assistant = _to_message_public(assistant_message)
    return ChatResponse(
        user_message=_to_message_public(user_message),
        assistant_message=assistant,
        answer=assistant.content,
        sources=assistant.sources,
        support_status=assistant.support_status or compute_support_status(assistant.content, assistant.sources),
    )
