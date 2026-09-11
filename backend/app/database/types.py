from __future__ import annotations

from sqlalchemy import JSON, TypeDecorator
from sqlalchemy.engine import Dialect


class EmbeddingVector(TypeDecorator):
    """JSON on SQLite (tests); pgvector on PostgreSQL."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect):
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            from app.core.config import settings

            return dialect.type_descriptor(Vector(settings.embedding_dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect: Dialect):
        return value

    def process_result_value(self, value, dialect: Dialect):
        return value
