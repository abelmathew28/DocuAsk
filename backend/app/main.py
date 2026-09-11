from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import limiter

configure_logging(settings.APP_DEBUG)
logger = get_logger("app")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_sqlite:
        from app.database.base import Base
        from app.database.session import engine
        from app.models import Conversation, Document, Message, User  # noqa: F401

        Base.metadata.create_all(bind=engine)
        from sqlalchemy import inspect, text

        inspector = inspect(engine)
        if "documents" in inspector.get_table_names():
            existing = {column["name"] for column in inspector.get_columns("documents")}
            alters = []
            if "is_starred" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN is_starred BOOLEAN DEFAULT 0")
            if "summary" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN summary TEXT")
            if "suggested_questions" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN suggested_questions TEXT")
            if "document_type" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN document_type VARCHAR(20) DEFAULT 'pdf'")
            if "title" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN title VARCHAR(255)")
            if "author" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN author VARCHAR(255)")
            if "processing_stage" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN processing_stage VARCHAR(40)")
            if "intelligence" not in existing:
                alters.append("ALTER TABLE documents ADD COLUMN intelligence TEXT")
            if alters:
                with engine.begin() as connection:
                    for statement in alters:
                        connection.execute(text(statement))
        if "document_chunks" in inspector.get_table_names():
            existing = {column["name"] for column in inspector.get_columns("document_chunks")}
            alters = []
            if "heading" not in existing:
                alters.append("ALTER TABLE document_chunks ADD COLUMN heading VARCHAR(255)")
            if "section" not in existing:
                alters.append("ALTER TABLE document_chunks ADD COLUMN section VARCHAR(255)")
            if "chunk_type" not in existing:
                alters.append("ALTER TABLE document_chunks ADD COLUMN chunk_type VARCHAR(20) DEFAULT 'text'")
            if "bbox" not in existing:
                alters.append("ALTER TABLE document_chunks ADD COLUMN bbox TEXT")
            if alters:
                with engine.begin() as connection:
                    for statement in alters:
                        connection.execute(text(statement))
        if "conversations" in inspector.get_table_names():
            existing = {column["name"] for column in inspector.get_columns("conversations")}
            alters = []
            if "scope" not in existing:
                alters.append("ALTER TABLE conversations ADD COLUMN scope VARCHAR(20) DEFAULT 'document'")
            if "document_ids" not in existing:
                alters.append("ALTER TABLE conversations ADD COLUMN document_ids TEXT")
            if alters:
                with engine.begin() as connection:
                    for statement in alters:
                        connection.execute(text(statement))
        if "message_sources" in inspector.get_table_names():
            existing = {column["name"] for column in inspector.get_columns("message_sources")}
            if "document_id" not in existing:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE message_sources ADD COLUMN document_id VARCHAR(36)"))
        logger.info("sqlite_schema_ready")
    _ensure_demo_user()
    _warm_ai_backends()
    yield


def _warm_ai_backends() -> None:
    """Load local embedding model once so the first Ask is not a cold start."""
    try:
        from app.ai.factory import get_ai_provider

        provider = get_ai_provider()
        provider.embed(["warmup"])
        logger.info("ai_backends_warmed")
    except Exception as exc:
        logger.warning("ai_warmup_skipped", error=str(exc))


def _ensure_demo_user() -> None:
    if not settings.DEMO_PASSWORD:
        return
    from app.core.security import hash_password
    from app.database.session import SessionLocal
    from app.models.user import User
    from app.repositories.user_repository import UserRepository

    db = SessionLocal()
    try:
        users = UserRepository(db)
        email = settings.DEMO_EMAIL.lower().strip()
        if users.get_by_email(email):
            return
        users.create(
            User(
                name="Abel",
                email=email,
                password_hash=hash_password(settings.DEMO_PASSWORD),
            )
        )
        logger.info("demo_user_created", email=email)
    finally:
        user = users.get_by_email(email)
        if user and settings.APP_ENV.lower() != "test":
            try:
                from app.services.demo_seed import ensure_demo_handbook

                ensure_demo_handbook(db, user)
            except Exception as exc:
                logger.error("demo_handbook_failed", error=str(exc))
        db.close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="DocuAsk API",
        description="AI document intelligence backend",
        version="1.0.0",
        docs_url="/api/docs" if settings.is_development else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    application.state.limiter = limiter
    application.add_middleware(SlowAPIMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/api/health")
    def health():
        return {
            "status": "ok",
            "service": "docuask",
            "embeddings": settings.EMBEDDING_PROVIDER,
            "llm": settings.LLM_PROVIDER,
            "reranker": settings.RERANKER,
            "formats": ["pdf", "docx", "txt"],
        }

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        logger.warning("app_error", code=exc.code, message=exc.message, status=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code, "errors": exc.details or None},
        )

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, _exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please wait a moment and try again.",
                "code": "rate_limited",
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Please check the submitted information.",
                "code": "validation_error",
                "errors": exc.errors() if settings.is_development else None,
            },
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_handler(_request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": "http_error"})

    @application.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception):
        logger.error("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Something went wrong. Please try again.", "code": "server_error"},
        )

    return application


app = create_app()
