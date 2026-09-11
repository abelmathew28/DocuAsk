from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, document_id: str, user_id: str) -> Optional[Document]:
        return self.db.scalar(
            select(Document).where(Document.id == document_id, Document.user_id == user_id)
        )

    def list_for_user(
        self,
        user_id: str,
        query: Optional[str] = None,
        status: Optional[str] = None,
        starred: Optional[bool] = None,
        sort: str = "created_at",
        order: str = "desc",
    ) -> List[Document]:
        stmt = select(Document).where(Document.user_id == user_id)
        if query:
            like = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(Document.name.ilike(like), Document.original_filename.ilike(like))
            )
        if status:
            stmt = stmt.where(Document.status == status)
        if starred is True:
            stmt = stmt.where(Document.is_starred.is_(True))

        sort_column = {
            "name": Document.name,
            "file_size": Document.file_size,
            "page_count": Document.page_count,
            "created_at": Document.created_at,
        }.get(sort, Document.created_at)
        stmt = stmt.order_by(sort_column.desc() if order == "desc" else sort_column.asc())
        return list(self.db.scalars(stmt).all())

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def save(self, document: Document) -> Document:
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()

    def count_for_user(self, user_id: str) -> int:
        return self.db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user_id)) or 0

    def storage_for_user(self, user_id: str) -> int:
        return self.db.scalar(select(func.coalesce(func.sum(Document.file_size), 0)).where(Document.user_id == user_id)) or 0

    def replace_chunks(self, document_id: str, chunks: List[DocumentChunk]) -> None:
        existing = self.db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id)).all()
        for chunk in existing:
            self.db.delete(chunk)
        for chunk in chunks:
            self.db.add(chunk)
        self.db.commit()

    def list_chunks(self, document_id: str, user_id: str) -> List[DocumentChunk]:
        return list(
            self.db.scalars(
                select(DocumentChunk).where(
                    DocumentChunk.document_id == document_id,
                    DocumentChunk.user_id == user_id,
                )
            ).all()
        )
