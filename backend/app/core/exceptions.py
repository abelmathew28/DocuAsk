from __future__ import annotations

from typing import Any, Dict, Optional


class AppError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__(message, status_code=401, code="unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "You do not have permission to access this resource.") -> None:
        super().__init__(message, status_code=403, code="forbidden")


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, status_code=404, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists.") -> None:
        super().__init__(message, status_code=409, code="conflict")


class ValidationAppError(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, status_code=422, code="validation_error", details=details)


class RateLimitError(AppError):
    def __init__(self, message: str = "Too many requests. Please try again later.") -> None:
        super().__init__(message, status_code=429, code="rate_limited")


class ProviderError(AppError):
    def __init__(self, message: str = "The AI provider is currently unavailable.") -> None:
        super().__init__(message, status_code=503, code="provider_unavailable")
