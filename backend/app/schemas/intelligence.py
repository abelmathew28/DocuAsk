from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    document_ids: List[str] = []
    conversation_id: Optional[str] = None


class CompareRequest(BaseModel):
    document_a_id: str
    document_b_id: str
    question: str = Field(default="", max_length=4000)
    conversation_id: Optional[str] = None


class ExtractRequest(BaseModel):
    question: str = Field(default="Extract dates, deadlines, requirements, contacts, and amounts.", max_length=4000)
    document_ids: List[str] = []
    fields: List[str] = []
    conversation_id: Optional[str] = None


class SummarizeRequest(BaseModel):
    kind: Literal["quick", "detailed", "key_points", "section"] = "quick"
    document_ids: List[str] = []
    focus: str = Field(default="", max_length=2000)
    conversation_id: Optional[str] = None
