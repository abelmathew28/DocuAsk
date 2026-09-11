from __future__ import annotations

import math
import re
from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.hybrid_search import keyword_score, reciprocal_rank_fusion
from app.ai.reranker import get_reranker
from app.ai.types import RetrievedChunk
from app.core.config import settings
from app.models.document import DocumentChunk

MIN_RELEVANCE = 0.18


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class RetrievalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.reranker = get_reranker()

    def search(
        self,
        user_id: str,
        query_embedding: List[float],
        document_ids: Optional[Sequence[str]] = None,
        query: Optional[str] = None,
        top_k: Optional[int] = None,
        candidates: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        ids = list(document_ids) if document_ids is not None else None
        if ids is not None and not ids:
            return []
        limit = candidates or settings.RETRIEVAL_CANDIDATES
        keep = top_k or settings.RERANK_TOP_K or settings.TOP_K_RESULTS
        if settings.is_sqlite:
            semantic = self._search_sqlite(user_id, query_embedding, ids, limit)
            keyword = self._keyword_sqlite(user_id, query or "", ids, limit) if query else []
        else:
            semantic = self._search_pgvector(user_id, query_embedding, ids, limit)
            keyword = self._keyword_postgres(user_id, query or "", ids, limit) if query else []
        fused = reciprocal_rank_fusion([semantic, keyword]) if keyword else semantic
        reranked = self.reranker.rerank(query or "", fused, keep)
        return reranked

    def expand_same_pages(
        self,
        user_id: str,
        seeds: List[RetrievedChunk],
        document_ids: Optional[Sequence[str]] = None,
    ) -> List[RetrievedChunk]:
        if not seeds:
            return []
        pages = {(chunk.document_id, chunk.page_number) for chunk in seeds}
        by_id = {chunk.id: chunk for chunk in seeds}
        ids = list(document_ids) if document_ids is not None else list({chunk.document_id for chunk in seeds})
        for chunk in self._load_chunks(user_id, ids):
            if (chunk.document_id, chunk.page_number) in pages and chunk.id not in by_id:
                by_id[chunk.id] = self._model_chunk(chunk, 0.32)
        return sorted(by_id.values(), key=lambda item: (item.page_number, item.chunk_index))

    def _search_pgvector(
        self,
        user_id: str,
        query_embedding: List[float],
        document_ids: Optional[List[str]],
        limit: int,
    ) -> List[RetrievedChunk]:
        from sqlalchemy import text

        filters = "c.user_id = :user_id AND c.embedding IS NOT NULL"
        params = {
            "embedding": str(query_embedding),
            "user_id": user_id,
            "limit": limit,
        }
        if document_ids is not None:
            filters += " AND c.document_id = ANY(:document_ids)"
            params["document_ids"] = list(document_ids)
        sql = text(
            f"""
            SELECT c.id, c.document_id, d.name AS document_name, c.page_number, c.text,
                   c.heading, c.chunk_type, c.bbox, c.chunk_index,
                   1 - (c.embedding <=> :embedding) AS score
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE {filters}
            ORDER BY c.embedding <=> :embedding
            LIMIT :limit
            """
        )
        try:
            rows = self.db.execute(sql, params).mappings()
        except Exception:
            sql = text(
                f"""
                SELECT c.id, c.document_id, d.name AS document_name, c.page_number, c.text,
                       1 - (c.embedding <=> :embedding) AS score
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE {filters}
                ORDER BY c.embedding <=> :embedding
                LIMIT :limit
                """
            )
            rows = self.db.execute(sql, params).mappings()
        return [self._row_chunk(row) for row in rows]

    def _keyword_postgres(
        self,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]],
        limit: int,
    ) -> List[RetrievedChunk]:
        from sqlalchemy import text

        if not query.strip():
            return []
        filters = "c.user_id = :user_id"
        params = {"query": query, "user_id": user_id, "limit": limit}
        if document_ids is not None:
            filters += " AND c.document_id = ANY(:document_ids)"
            params["document_ids"] = list(document_ids)
        sql = text(
            f"""
            SELECT c.id, c.document_id, d.name AS document_name, c.page_number, c.text,
                   c.heading, c.chunk_type, c.bbox, c.chunk_index,
                   ts_rank_cd(to_tsvector('english', c.text), plainto_tsquery('english', :query)) AS score
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE {filters}
              AND to_tsvector('english', c.text) @@ plainto_tsquery('english', :query)
            ORDER BY score DESC
            LIMIT :limit
            """
        )
        try:
            rows = self.db.execute(sql, params).mappings()
            return [self._row_chunk(row) for row in rows]
        except Exception:
            return self._keyword_sqlite(user_id, query, document_ids, limit)

    def _search_sqlite(
        self,
        user_id: str,
        query_embedding: List[float],
        document_ids: Optional[List[str]],
        limit: int,
    ) -> List[RetrievedChunk]:
        chunks = self._load_chunks(user_id, document_ids)
        scored: List[RetrievedChunk] = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            scored.append(self._model_chunk(chunk, _cosine(query_embedding, chunk.embedding)))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def _keyword_sqlite(
        self,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]],
        limit: int,
    ) -> List[RetrievedChunk]:
        if not query.strip():
            return []
        chunks = self._load_chunks(user_id, document_ids)
        scored = []
        for chunk in chunks:
            score = keyword_score(query, f"{chunk.heading or ''} {chunk.text}")
            if score <= 0:
                continue
            scored.append(self._model_chunk(chunk, score))
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def _load_chunks(self, user_id: str, document_ids: Optional[List[str]]) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.document))
            .where(DocumentChunk.user_id == user_id)
        )
        if document_ids is not None:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
        return list(self.db.scalars(stmt).all())

    def _model_chunk(self, chunk: DocumentChunk, score: float) -> RetrievedChunk:
        name = chunk.document.name if chunk.document else ""
        return RetrievedChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            document_name=name,
            page_number=chunk.page_number,
            text=chunk.text,
            score=score,
            heading=getattr(chunk, "heading", None),
            chunk_type=getattr(chunk, "chunk_type", None) or "text",
            bbox=getattr(chunk, "bbox", None),
            chunk_index=getattr(chunk, "chunk_index", 0) or 0,
        )

    def _row_chunk(self, row) -> RetrievedChunk:
        return RetrievedChunk(
            id=row["id"],
            document_id=row["document_id"],
            document_name=row["document_name"],
            page_number=row["page_number"],
            text=row["text"],
            score=float(row["score"] or 0),
            heading=row.get("heading") if hasattr(row, "get") else None,
            chunk_type=(row.get("chunk_type") if hasattr(row, "get") else None) or "text",
            bbox=row.get("bbox") if hasattr(row, "get") else None,
            chunk_index=int(row.get("chunk_index") or 0) if hasattr(row, "get") else 0,
        )
