from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "DocuAsk"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    API_V1_PREFIX: str = "/api"
    FRONTEND_URL: str = "http://localhost:4200"
    CORS_ORIGINS: str = "http://localhost:4200"

    DATABASE_URL: str = "postgresql+psycopg2://docuask:docuask@localhost:5432/docuask"

    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536
    OPENAI_MAX_OUTPUT_TOKENS: int = 800

    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    LOCAL_EMBEDDING_DIMENSIONS: int = 384
    LLM_PROVIDER: str = "auto"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    CHUNK_SIZE: int = 900
    CHUNK_OVERLAP: int = 150
    TOP_K_RESULTS: int = 6
    RETRIEVAL_CANDIDATES: int = 20
    RERANK_TOP_K: int = 6
    RERANKER: str = "lexical"
    MAX_CONTEXT_CHARS: int = 12000
    CONVERSATION_HISTORY_MESSAGES: int = 6

    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "./storage/uploads"

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = ""

    AUTH_RATE_LIMIT: str = "10/minute"
    UPLOAD_RATE_LIMIT: str = "20/hour"
    CHAT_RATE_LIMIT: str = "30/minute"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@docuask.app"

    DEMO_EMAIL: str = "demo@docuask.app"
    DEMO_PASSWORD: str = ""

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("JWT_SECRET must be set")
        return value

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() in {"development", "dev", "local", "test"}

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def embedding_dimensions(self) -> int:
        if self.EMBEDDING_PROVIDER.lower() == "openai":
            return self.OPENAI_EMBEDDING_DIMENSIONS
        return self.LOCAL_EMBEDDING_DIMENSIONS


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
