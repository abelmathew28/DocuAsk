from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_documents: int
    questions_asked: int
    conversations: int
    storage_used: int
    ai_requests: int
    average_response_ms: Optional[float] = None


class AnalyticsSummary(BaseModel):
    documents_uploaded: int
    questions_asked: int
    total_conversations: int
    ai_requests: int
    average_response_time_ms: Optional[float] = None
