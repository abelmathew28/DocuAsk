from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.logging import get_logger
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.storage.base import get_storage

logger = get_logger("demo")

DEMO_FILENAME = "employee-handbook-demo.pdf"
DEMO_NAME = "Employee Handbook"

HE_CALENDAR_FILENAME = "fall-2026-academic-calendar.txt"
HE_CALENDAR_NAME = "Fall 2026 Academic Calendar"
HE_HANDBOOK_FILENAME = "student-handbook-excerpt.txt"
HE_HANDBOOK_NAME = "Student Handbook Excerpt"


def ensure_demo_handbook(db, user: User) -> None:
    """Seed classic handbook PDF plus higher-education sample documents."""
    _ensure_pdf_handbook(db, user)
    _ensure_text_demo(
        db,
        user,
        filename=HE_CALENDAR_FILENAME,
        name=HE_CALENDAR_NAME,
        relative=("demo-data", "documents", HE_CALENDAR_FILENAME),
        mime="text/plain",
    )
    _ensure_text_demo(
        db,
        user,
        filename=HE_HANDBOOK_FILENAME,
        name=HE_HANDBOOK_NAME,
        relative=("demo-data", "documents", HE_HANDBOOK_FILENAME),
        mime="text/plain",
    )


def _ensure_pdf_handbook(db, user: User) -> None:
    documents = DocumentRepository(db)
    existing = [
        item
        for item in documents.list_for_user(user.id)
        if item.original_filename == DEMO_FILENAME or item.name == DEMO_NAME
    ]
    ready = [item for item in existing if item.status == DocumentStatus.READY.value]
    if ready:
        return
    failed = [item for item in existing if item.status == DocumentStatus.FAILED.value]
    if failed:
        from app.ai.document_processor import DocumentProcessor

        DocumentProcessor(db, get_storage()).process(failed[0].id, user.id)
        return
    if existing:
        return

    pdf_path = _handbook_path()
    data = pdf_path.read_bytes()
    document = Document(
        user_id=user.id,
        name=DEMO_NAME,
        original_filename=DEMO_FILENAME,
        storage_path="pending",
        file_size=len(data),
        mime_type="application/pdf",
        status=DocumentStatus.PROCESSING.value,
        document_type="pdf",
    )
    documents.create(document)
    storage = get_storage()
    document.storage_path = storage.save(user.id, document.id, f"{document.id}.pdf", data)
    documents.save(document)

    from app.ai.document_processor import DocumentProcessor

    logger.info("demo_handbook_indexing", document_id=document.id)
    DocumentProcessor(db, storage).process(document.id, user.id)


def _ensure_text_demo(
    db,
    user: User,
    *,
    filename: str,
    name: str,
    relative: tuple[str, ...],
    mime: str,
) -> None:
    documents = DocumentRepository(db)
    existing = [
        item
        for item in documents.list_for_user(user.id)
        if item.original_filename == filename or item.name == name
    ]
    if any(item.status == DocumentStatus.READY.value for item in existing):
        return
    failed = [item for item in existing if item.status == DocumentStatus.FAILED.value]
    if failed:
        from app.ai.document_processor import DocumentProcessor

        DocumentProcessor(db, get_storage()).process(failed[0].id, user.id)
        return
    if existing:
        return

    path = _project_root().joinpath(*relative)
    if not path.exists():
        logger.warning("demo_text_missing", path=str(path))
        return
    data = path.read_bytes()
    document = Document(
        user_id=user.id,
        name=name,
        original_filename=filename,
        storage_path="pending",
        file_size=len(data),
        mime_type=mime,
        status=DocumentStatus.PROCESSING.value,
        document_type="txt",
    )
    documents.create(document)
    storage = get_storage()
    document.storage_path = storage.save(user.id, document.id, f"{document.id}.txt", data)
    documents.save(document)

    from app.ai.document_processor import DocumentProcessor

    logger.info("demo_text_indexing", document_id=document.id, name=name)
    DocumentProcessor(db, storage).process(document.id, user.id)


def _handbook_path() -> Path:
    dest = _project_root() / "demo" / DEMO_FILENAME
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    generator = dest.parent / "generate_handbook.py"
    spec = importlib.util.spec_from_file_location("docuask_handbook", generator)
    if spec is None or spec.loader is None:
        raise RuntimeError("Demo handbook generator is missing.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.build_handbook(dest)
    return dest


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "demo" / "generate_handbook.py").exists() or (parent / "demo" / DEMO_FILENAME).exists():
            return parent
        if (parent / "demo-data" / "documents").exists():
            return parent
    return here.parents[3]
