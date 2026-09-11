from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.usage_repository import UsageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import AnalyticsSummary, DashboardStats
from app.storage.base import get_storage


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.documents = DocumentRepository(db)
        self.conversations = ConversationRepository(db)
        self.usage = UsageRepository(db)

    def update(self, user: User, name=None, theme=None, default_model=None) -> User:
        if name is not None:
            user.name = name.strip()
        if theme is not None:
            user.theme = theme
        if default_model is not None:
            user.default_model = default_model
        return self.users.save(user)

    def delete_account(self, user: User) -> None:
        storage = get_storage()
        for document in list(user.documents):
            try:
                storage.delete(document.storage_path)
            except Exception:
                pass
        self.users.delete(user)

    def dashboard_stats(self, user: User) -> DashboardStats:
        questions = self.usage.questions_asked(user.id)
        ai_requests = self.usage.count(user.id, "ai_request")
        avg = self.usage.average_duration(user.id, "ai_request")
        return DashboardStats(
            total_documents=self.documents.count_for_user(user.id),
            questions_asked=questions,
            conversations=self.conversations.count_for_user(user.id),
            storage_used=self.documents.storage_for_user(user.id),
            ai_requests=ai_requests,
            average_response_ms=avg,
        )

    def analytics(self, user: User) -> AnalyticsSummary:
        stats = self.dashboard_stats(user)
        return AnalyticsSummary(
            documents_uploaded=stats.total_documents,
            questions_asked=stats.questions_asked,
            total_conversations=stats.conversations,
            ai_requests=stats.ai_requests,
            average_response_time_ms=stats.average_response_ms,
        )
