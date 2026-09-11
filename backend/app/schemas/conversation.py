from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document: str
    page: int
    excerpt: str
    relevance_score: Optional[float] = None
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None


class MessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    feedback: Optional[str] = None
    created_at: datetime
    sources: List[SourcePublic] = []
    support_status: Optional[Literal["supported", "partially_supported", "not_found"]] = None


class ConversationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    document_name: Optional[str] = None
    title: str
    preview: Optional[str] = None
    scope: str = "document"
    document_ids: List[str] = []
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationPublic):
    messages: List[MessagePublic] = []


class ConversationCreate(BaseModel):
    document_id: Optional[str] = None
    document_ids: List[str] = []
    scope: Literal["document", "selected", "library"] = "document"
    title: Optional[str] = Field(default=None, max_length=160)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope == "document" and not self.document_id:
            raise ValueError("Choose a document to ask.")
        if self.scope == "selected":
            ids = list(dict.fromkeys([*self.document_ids, *([self.document_id] if self.document_id else [])]))
            if len(ids) < 1:
                raise ValueError("Select at least one document.")
            self.document_ids = ids
            self.document_id = ids[0]
        return self


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    mode: Literal["ask", "research", "extract"] = "ask"


class ChatResponse(BaseModel):
    user_message: MessagePublic
    assistant_message: MessagePublic
    answer: str
    sources: List[SourcePublic]
    support_status: Literal["supported", "partially_supported", "not_found"] = "supported"


class FeedbackRequest(BaseModel):
    rating: str = Field(pattern="^(up|down)$")
