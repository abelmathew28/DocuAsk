from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(payload.name, payload.email, payload.password)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(payload.email, payload.password)


@router.post("/demo", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def demo_login(request: Request, db: Session = Depends(get_db)):
    return AuthService(db).demo_login()


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    AuthService(db).logout(payload.refresh_token)
    return MessageResponse(message="Signed out.")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    message = AuthService(db).forgot_password(payload.email)
    return MessageResponse(message=message)


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(payload.token, payload.password)
    return MessageResponse(message="Password updated. You can now sign in.")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    AuthService(db).change_password(current_user, payload.current_password, payload.new_password)
    return MessageResponse(message="Password updated.")
