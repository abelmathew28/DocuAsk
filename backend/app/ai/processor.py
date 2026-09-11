from __future__ import annotations

from typing import List, Protocol

from app.ai.office_parser import extract_docx_pages, extract_txt_pages
from app.ai.pdf_parser import extract_pdf_pages
from app.ai.types import PageText, TextChunk  # noqa: F401
from app.core.exceptions import ValidationAppError

from app.ai.chunking_service import chunk_pages

PDF_MIME = {"application/pdf", "application/x-pdf"}
DOCX_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
TXT_MIME = {"text/plain", "text/markdown"}


class DocumentExtractor(Protocol):
    def extract_pages(self, data: bytes) -> List[PageText]:
        ...


class PdfExtractor:
    def extract_pages(self, data: bytes) -> List[PageText]:
        return extract_pdf_pages(data)


class DocxExtractor:
    def extract_pages(self, data: bytes) -> List[PageText]:
        return extract_docx_pages(data)


class TxtExtractor:
    def extract_pages(self, data: bytes) -> List[PageText]:
        return extract_txt_pages(data)


def get_extractor(mime_type: str, filename: str = "") -> DocumentExtractor:
    mime = (mime_type or "").lower()
    name = (filename or "").lower()
    if mime in PDF_MIME or name.endswith(".pdf"):
        return PdfExtractor()
    if mime in DOCX_MIME or name.endswith(".docx"):
        return DocxExtractor()
    if mime in TXT_MIME or name.endswith(".txt") or name.endswith(".md"):
        return TxtExtractor()
    raise ValidationAppError("Only PDF, Word (.docx), and text files are supported right now.")
