from __future__ import annotations

import re

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import ValidationAppError

PDF_MIME = {"application/pdf", "application/x-pdf"}
DOCX_MIME = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
TXT_MIME = {"text/plain", "text/markdown", "application/octet-stream"}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def detect_kind(filename: str, content_type: str = "") -> str:
    name = (filename or "").lower()
    mime = (content_type or "").lower()
    if name.endswith(".pdf") or mime in PDF_MIME:
        return "pdf"
    if name.endswith(".docx") or mime in DOCX_MIME:
        return "docx"
    if name.endswith(".txt") or name.endswith(".md") or mime in {"text/plain", "text/markdown"}:
        return "txt"
    return ""


def mime_for_kind(kind: str) -> str:
    return {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }.get(kind, "application/octet-stream")


def extension_for_kind(kind: str) -> str:
    return {"pdf": ".pdf", "docx": ".docx", "txt": ".txt"}.get(kind, "")


def safe_filename(name: str, kind: str = "pdf") -> str:
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    ext = extension_for_kind(kind)
    lower = name.lower()
    if ext and not lower.endswith(ext):
        name = f"{name or 'document'}{ext}"
    return name[:180]


def validate_upload(file: UploadFile) -> str:
    filename = file.filename or ""
    kind = detect_kind(filename, file.content_type or "")
    if not kind:
        raise ValidationAppError("Only PDF, Word (.docx), and text files are supported.")
    header = file.file.read(8)
    file.file.seek(0)
    if kind == "pdf" and header[:5] != b"%PDF-":
        raise ValidationAppError("The file does not appear to be a valid PDF.")
    if kind == "docx" and header[:2] != b"PK":
        raise ValidationAppError("The file does not appear to be a valid Word document.")
    size = getattr(file, "size", None)
    if size and size > settings.MAX_UPLOAD_SIZE:
        raise ValidationAppError(
            f"File is too large. Maximum size is {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
        )
    return kind


def validate_pdf_upload(file: UploadFile) -> None:
    """Backward-compatible wrapper."""
    validate_upload(file)
