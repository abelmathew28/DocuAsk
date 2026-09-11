from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Authentication required.")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid access token.")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid access token.")
    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid access token.")
    return user
