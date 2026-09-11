from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, DashboardStats
from app.schemas.auth import MessageResponse, UserPublic, UserUpdate
from app.services.conversation_service import ConversationService
from app.services.user_service import UserService

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/users/me", response_model=UserPublic)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserService(db).update(
        current_user,
        name=payload.name,
        theme=payload.theme,
        default_model=payload.default_model,
    )


@router.delete("/users/me", response_model=MessageResponse)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    UserService(db).delete_account(current_user)
    return MessageResponse(message="Account deleted.")


@router.get("/users/me/stats", response_model=DashboardStats)
def stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserService(db).dashboard_stats(current_user)


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserService(db).analytics(current_user)


@router.delete("/users/me/conversations", response_model=MessageResponse)
def delete_all_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = ConversationService(db).delete_all(current_user)
    return MessageResponse(message=f"Deleted {count} conversations.")
