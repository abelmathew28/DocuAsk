from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError, ConflictError, NotFoundError, UnauthorizedError, ValidationAppError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token_value,
    generate_reset_token,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)
from app.models.user import RefreshToken, User
from app.repositories.user_repository import RefreshTokenRepository, UserRepository
from app.schemas.auth import TokenResponse, UserPublic
from app.services.email_service import EmailService

logger = get_logger("auth")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)
        self.email = EmailService()

    def register(self, name: str, email: str, password: str) -> TokenResponse:
        existing = self.users.get_by_email(email)
        if existing:
            raise ConflictError("An account with this email already exists.")
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=hash_password(password),
        )
        self.users.create(user)
        logger.info("user_registered", user_id=user.id)
        return self._issue_tokens(user)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account is disabled.")
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            self.users.save(user)
        logger.info("user_login", user_id=user.id)
        return self._issue_tokens(user)

    def demo_login(self) -> TokenResponse:
        if not settings.DEMO_PASSWORD:
            raise AppError("The public demo is not enabled on this server.", status_code=404, code="demo_disabled")
        return self.login(settings.DEMO_EMAIL, settings.DEMO_PASSWORD)

    def refresh(self, refresh_token: str) -> TokenResponse:
        record = self.tokens.get_valid(hash_token(refresh_token))
        if not record:
            raise UnauthorizedError("Invalid or expired refresh token.")
        user = self.users.get_by_id(record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Invalid or expired refresh token.")
        self.tokens.revoke(record)
        return self._issue_tokens(user)

    def logout(self, refresh_token: Optional[str]) -> None:
        if not refresh_token:
            return
        record = self.tokens.get_valid(hash_token(refresh_token))
        if record:
            self.tokens.revoke(record)

    def forgot_password(self, email: str) -> str:
        user = self.users.get_by_email(email)
        # Always succeed to avoid account enumeration.
        if not user:
            return "If an account exists for that email, a reset link has been sent."
        raw = generate_reset_token()
        user.password_reset_token = hash_token(raw)
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        self.users.save(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={raw}"
        self.email.send_password_reset(user.email, reset_url)
        logger.info("password_reset_requested", user_id=user.id)
        if settings.is_development:
            return reset_url
        return "If an account exists for that email, a reset link has been sent."

    def reset_password(self, token: str, password: str) -> None:
        user = self.users.get_by_reset_token(hash_token(token))
        if not user or not user.password_reset_expires:
            raise ValidationAppError("This reset link is invalid or has expired.")
        expires = user.password_reset_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise ValidationAppError("This reset link is invalid or has expired.")
        user.password_hash = hash_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        self.users.save(user)
        self.tokens.revoke_all_for_user(user.id)

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise ValidationAppError("Current password is incorrect.")
        user.password_hash = hash_password(new_password)
        self.users.save(user)
        self.tokens.revoke_all_for_user(user.id)

    def _issue_tokens(self, user: User) -> TokenResponse:
        access = create_access_token(user.id)
        refresh = create_refresh_token_value()
        self.tokens.create(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh),
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            user=UserPublic.model_validate(user),
        )
