from __future__ import annotations

import os
import re
from typing import Optional

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.ai.document_processor import DocumentProcessor
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError, ValidationAppError
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.usage_repository import UsageRepository
from app.storage.base import StorageBackend, get_storage
from app.utils.files import (
    extension_for_kind,
    mime_for_kind,
    safe_filename,
    validate_upload,
)

PDF_MIME = {"application/pdf", "application/x-pdf"}


class DocumentService:
    def __init__(self, db: Session, storage: Optional[StorageBackend] = None) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.usage = UsageRepository(db)
        self.storage = storage or get_storage()

    def list_documents(
        self,
        user: User,
        query: Optional[str] = None,
        status: Optional[str] = None,
        starred: Optional[bool] = None,
        sort: str = "created_at",
        order: str = "desc",
    ):
        return self.documents.list_for_user(
            user.id, query=query, status=status, starred=starred, sort=sort, order=order
        )

    def get_owned(self, user: User, document_id: str) -> Document:
        document = self.documents.get(document_id, user.id)
        if not document:
            raise NotFoundError("Document not found.")
        return document

    def upload(self, user: User, file: UploadFile, background: BackgroundTasks) -> Document:
        kind = validate_upload(file)
        data = file.file.read()
        if len(data) > settings.MAX_UPLOAD_SIZE:
            raise ValidationAppError(
                f"File is too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
            )
        if not data:
            raise ValidationAppError("The uploaded file is empty.")

        original = safe_filename(file.filename or f"document{extension_for_kind(kind)}", kind)
        display_name = os.path.splitext(original)[0]
        document = Document(
            user_id=user.id,
            name=display_name,
            original_filename=original,
            storage_path="pending",
            file_size=len(data),
            mime_type=mime_for_kind(kind),
            document_type=kind,
            status=DocumentStatus.UPLOADING.value,
            processing_stage="uploading",
        )
        self.documents.create(document)
        stored_name = f"{document.id}{extension_for_kind(kind)}"
        document.storage_path = self.storage.save(user.id, document.id, stored_name, data)
        document.status = DocumentStatus.PROCESSING.value
        document.processing_stage = "reading"
        self.documents.save(document)
        self.usage.record(user.id, "document_upload")
        background.add_task(self._process, document.id, user.id)
        return document

    def update(self, user: User, document_id: str, name: Optional[str] = None, is_starred: Optional[bool] = None) -> Document:
        document = self.get_owned(user, document_id)
        if name is not None:
            document.name = name.strip()
        if is_starred is not None:
            document.is_starred = is_starred
        return self.documents.save(document)

    def delete(self, user: User, document_id: str) -> None:
        document = self.get_owned(user, document_id)
        try:
            self.storage.delete(document.storage_path)
        except Exception:
            pass
        self.documents.delete(document)

    def file_bytes(self, user: User, document_id: str) -> bytes:
        document = self.get_owned(user, document_id)
        return self.storage.load(document.storage_path)

    def reprocess(self, user: User, document_id: str, background: BackgroundTasks) -> Document:
        document = self.get_owned(user, document_id)
        if document.status == DocumentStatus.PROCESSING.value:
            raise ValidationAppError("This document is already being processed.")
        document.status = DocumentStatus.PROCESSING.value
        document.processing_stage = "reading"
        document.error_message = None
        self.documents.save(document)
        background.add_task(self._process, document.id, user.id)
        return document

    def _process(self, document_id: str, user_id: str) -> None:
        from app.database.session import SessionLocal

        db = SessionLocal()
        try:
            DocumentProcessor(db, self.storage).process(document_id, user_id)
        finally:
            db.close()
