from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.chat import ChatService
from app.ai.comparison_service import ComparisonService
from app.ai.extraction_service import ExtractionService
from app.ai.research_service import ResearchService
from app.ai.summarization_service import SummarizationService
from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.conversation import Message, MessageRole, MessageSource
from app.models.document import DocumentStatus
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.conversation import ChatResponse, MessagePublic, SourcePublic
from app.schemas.intelligence import CompareRequest, ExtractRequest, ResearchRequest, SummarizeRequest
from app.core.exceptions import ValidationAppError

router = APIRouter(tags=["intelligence"])


@router.post("/research", response_model=ChatResponse)
def research(
    payload: ResearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = ChatService(db)
    ids = _ready_ids(db, current_user.id, payload.document_ids)
    answer, chunks = ResearchService(chat).run(
        current_user.id,
        payload.question,
        ids if payload.document_ids else None,
    )
    return _persist_or_ephemeral(db, current_user, payload.conversation_id, payload.question, answer, chunks, ids)


@router.post("/compare", response_model=ChatResponse)
def compare(
    payload: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = ChatService(db)
    question = payload.question or "Compare these two documents."
    answer, chunks = ComparisonService(chat).run(
        current_user.id,
        payload.document_a_id,
        payload.document_b_id,
        payload.question,
    )
    return _persist_or_ephemeral(
        db,
        current_user,
        payload.conversation_id,
        question,
        answer,
        chunks,
        [payload.document_a_id, payload.document_b_id],
    )


@router.post("/extract", response_model=ChatResponse)
def extract(
    payload: ExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = ChatService(db)
    ids = _ready_ids(db, current_user.id, payload.document_ids)
    question = payload.question
    if payload.fields:
        question = f"Extract {', '.join(payload.fields)}. {payload.question}".strip()
    answer, chunks = ExtractionService(chat).run(
        current_user.id,
        question,
        ids if payload.document_ids else None,
    )
    return _persist_or_ephemeral(db, current_user, payload.conversation_id, question, answer, chunks, ids)


@router.post("/summarize", response_model=ChatResponse)
def summarize(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = ChatService(db)
    ids = _ready_ids(db, current_user.id, payload.document_ids)
    answer, chunks = SummarizationService(chat).run(
        current_user.id,
        ids if payload.document_ids else None,
        payload.kind,
        payload.focus,
    )
    question = payload.focus or f"{payload.kind.replace('_', ' ')} summary"
    return _persist_or_ephemeral(db, current_user, payload.conversation_id, question, answer, chunks, ids)


@router.get("/extract/export")
def extract_export(
    document_ids: Optional[str] = None,
    fields: Optional[str] = None,
    fmt: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi.responses import JSONResponse, PlainTextResponse

    chat = ChatService(db)
    ids = [item.strip() for item in (document_ids or "").split(",") if item.strip()]
    field_list = [item.strip() for item in (fields or "").split(",") if item.strip()]
    data = ExtractionService(chat).structured(current_user.id, ids or None, field_list)
    if fmt == "csv":
        lines = ["field,value,document,page"]
        for row in data["rows"]:
            value = str(row["value"]).replace('"', '""')
            lines.append(f'{row["field"]},"{value}",{row["document"]},{row["page"] or ""}')
        return PlainTextResponse("\n".join(lines), media_type="text/csv")
    return JSONResponse(data)


def _ready_ids(db: Session, user_id: str, document_ids: List[str]) -> List[str]:
    if not document_ids:
        return []
    documents = DocumentRepository(db)
    ready = []
    for document_id in document_ids:
        document = documents.get(document_id, user_id)
        if document and document.status == DocumentStatus.READY.value:
            ready.append(document.id)
    if document_ids and not ready:
        raise ValidationAppError("None of the selected documents are ready yet.")
    return ready


def _persist_or_ephemeral(db, user, conversation_id, question, answer, chunks, document_ids) -> ChatResponse:
    sources = [
        SourcePublic(
            document=chunk.document_name,
            page=chunk.page_number,
            excerpt=(chunk.text or "")[:280],
            relevance_score=round(chunk.score, 4),
            chunk_id=chunk.id,
            document_id=chunk.document_id,
        )
        for chunk in chunks[:6]
    ]
    if not conversation_id:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return ChatResponse(
            user_message=MessagePublic(id="ephemeral-user", role="user", content=question, created_at=now, sources=[]),
            assistant_message=MessagePublic(
                id="ephemeral-assistant",
                role="assistant",
                content=answer,
                created_at=now,
                sources=sources,
            ),
            answer=answer,
            sources=sources,
        )

    conversations = ConversationRepository(db)
    conversation = conversations.get(conversation_id, user.id)
    if not conversation:
        raise ValidationAppError("Conversation not found.")
    user_message = Message(conversation_id=conversation.id, role=MessageRole.USER.value, content=question)
    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT.value,
        content=answer,
        sources=[
            MessageSource(
                document_chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                excerpt=(chunk.text or "")[:280],
                relevance_score=round(chunk.score, 4),
            )
            for chunk in chunks[:6]
        ],
    )
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    from app.services.conversation_service import _to_chat_response

    return _to_chat_response(user_message, assistant_message)
