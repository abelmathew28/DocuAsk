from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationPublic,
    ConversationUpdate,
    FeedbackRequest,
    MessagePublic,
)
from app.services.conversation_service import ConversationService, _to_message_public

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=List[ConversationPublic])
def list_conversations(
    document_id: Optional[str] = Query(default=None),
    scope: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ConversationService(db).list(current_user, document_id, scope)


@router.post("", response_model=ConversationPublic)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationService(db)
    conversation = service.create(
        current_user,
        payload.document_id,
        payload.title,
        payload.scope,
        payload.document_ids,
    )
    return service.detail(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationService(db)
    return service.detail(service.get(current_user, conversation_id))


@router.patch("/{conversation_id}", response_model=ConversationPublic)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationService(db)
    conversation = service.rename(current_user, conversation_id, payload.title)
    return service.detail(conversation)


@router.get("/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ConversationService(db)
    conversation = service.get(current_user, conversation_id)
    lines = [
        f"# {conversation.title}",
        f"Scope: {conversation.scope or 'document'}",
        f"Document: {conversation.document.name if conversation.document else conversation.document_id}",
        "",
    ]
    for message in conversation.messages:
        label = "You" if message.role == "user" else "DocuAsk"
        lines.append(f"## {label}")
        lines.append(message.content)
        if message.sources:
            lines.append("")
            lines.append("Sources:")
            for source in message.sources:
                lines.append(f"- {source.document_name} — page {source.page_number}")
        lines.append("")
    body = "\n".join(lines)
    filename = f"{conversation.title.replace(' ', '-').lower()[:48] or 'conversation'}.md"
    return Response(
        content=body,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{conversation_id}", response_model=MessageResponse)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ConversationService(db).delete(current_user, conversation_id)
    return MessageResponse(message="Conversation deleted.")


@router.post("/{conversation_id}/messages", response_model=ChatResponse)
@limiter.limit(settings.CHAT_RATE_LIMIT)
def send_message(
    request: Request,
    conversation_id: str,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ConversationService(db).ask(current_user, conversation_id, payload.content, payload.mode)


@router.post("/{conversation_id}/regenerate", response_model=ChatResponse)
@limiter.limit(settings.CHAT_RATE_LIMIT)
def regenerate(
    request: Request,
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ConversationService(db).regenerate(current_user, conversation_id)


@router.post("/{conversation_id}/messages/{message_id}/feedback", response_model=MessagePublic)
def feedback(
    conversation_id: str,
    message_id: str,
    payload: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = ConversationService(db).feedback(current_user, message_id, payload.rating)
    return _to_message_public(message)
