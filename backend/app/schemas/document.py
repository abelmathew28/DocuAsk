from __future__ import annotations

from datetime import datetime
import json
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.document import DocumentStatus


class DocumentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    original_filename: str
    file_size: int
    mime_type: str
    document_type: str = "pdf"
    title: Optional[str] = None
    page_count: Optional[int] = None
    status: DocumentStatus
    processing_stage: Optional[str] = None
    error_message: Optional[str] = None
    is_starred: bool = False
    summary: Optional[str] = None
    suggested_questions: List[str] = []
    intelligence: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("suggested_questions", mode="before")
    @classmethod
    def parse_questions(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (TypeError, json.JSONDecodeError):
            return []

    @field_validator("intelligence", mode="before")
    @classmethod
    def parse_intelligence(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except (TypeError, json.JSONDecodeError):
            return None


class DocumentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_starred: Optional[bool] = None


class DocumentStatusPublic(BaseModel):
    id: str
    status: DocumentStatus
    processing_stage: Optional[str] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None
