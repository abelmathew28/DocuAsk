from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.conversation import Message, MessageRole
from app.models.usage import UsageEvent


class UsageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, user_id: str, event_type: str, duration_ms: Optional[int] = None) -> UsageEvent:
        event = UsageEvent(user_id=user_id, event_type=event_type, duration_ms=duration_ms)
        self.db.add(event)
        self.db.commit()
        return event

    def count(self, user_id: str, event_type: str) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(UsageEvent)
            .where(UsageEvent.user_id == user_id, UsageEvent.event_type == event_type)
        ) or 0

    def average_duration(self, user_id: str, event_type: str) -> Optional[float]:
        value = self.db.scalar(
            select(func.avg(UsageEvent.duration_ms)).where(
                UsageEvent.user_id == user_id,
                UsageEvent.event_type == event_type,
                UsageEvent.duration_ms.is_not(None),
            )
        )
        return float(value) if value is not None else None

    def questions_asked(self, user_id: str) -> int:
        return self.db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Message.conversation)
            .where(Message.role == MessageRole.USER.value, Message.conversation.has(user_id=user_id))
        ) or 0
