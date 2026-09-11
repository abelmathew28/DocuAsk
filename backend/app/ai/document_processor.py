from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.chunking_service import chunk_pages
from app.ai.embeddings import EmbeddingService
from app.ai.factory import get_ai_provider
from app.ai.metadata import dump_intelligence, extract_intelligence
from app.ai.processor import get_extractor
from app.core.exceptions import ProviderError, ValidationAppError
from app.core.logging import get_logger
from app.database.base import utcnow
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.storage.base import StorageBackend, get_storage

logger = get_logger("ai.processor")


class DocumentProcessor:
    def __init__(self, db: Session, storage: StorageBackend | None = None) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.storage = storage or get_storage()

    def process(self, document_id: str, user_id: str) -> None:
        document = self.documents.get(document_id, user_id)
        if not document:
            logger.error("process_missing_document", document_id=document_id)
            return

        document.status = DocumentStatus.PROCESSING.value
        document.processing_stage = "reading"
        document.processing_started_at = utcnow()
        document.error_message = None
        self.documents.save(document)

        try:
            data = self.storage.load(document.storage_path)
            extractor = get_extractor(document.mime_type, document.original_filename)
            pages = extractor.extract_pages(data)
            document.page_count = len(pages)
            document.processing_stage = "understanding"
            self.documents.save(document)

            intelligence = extract_intelligence(pages, document.original_filename)
            document.title = intelligence.get("title") or document.name
            document.intelligence = dump_intelligence(intelligence)

            chunks = chunk_pages(pages)
            if not chunks:
                raise ValidationAppError("The document did not contain enough text to index.")

            document.processing_stage = "indexing"
            self.documents.save(document)

            provider = get_ai_provider()
            embeddings = EmbeddingService(provider).embed_documents([chunk.text for chunk in chunks])
            records = [
                DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    heading=chunk.heading,
                    section=chunk.section,
                    chunk_type=chunk.chunk_type,
                    bbox=chunk.bbox,
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, embeddings)
            ]
            self.documents.replace_chunks(document.id, records)

            from app.utils.insights import dump_questions, extractive_summary, suggested_questions

            document.summary = extractive_summary(pages)
            document.suggested_questions = dump_questions(suggested_questions(pages))
            document.status = DocumentStatus.READY.value
            document.processing_stage = "ready"
            document.processing_finished_at = utcnow()
            self.documents.save(document)
            logger.info(
                "document_processed",
                document_id=document.id,
                pages=document.page_count,
                chunks=len(records),
            )
        except ValidationAppError as exc:
            self._fail(document, exc.message)
        except ProviderError as exc:
            self._fail(document, exc.message)
        except Exception as exc:
            logger.error("document_processing_failed", document_id=document.id, error=str(exc))
            self._fail(document, "Document processing failed. Please try uploading again.")

    def _fail(self, document: Document, message: str) -> None:
        document.status = DocumentStatus.FAILED.value
        document.processing_stage = "failed"
        document.error_message = message
        document.processing_finished_at = utcnow()
        self.documents.save(document)
