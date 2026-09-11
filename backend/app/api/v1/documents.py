from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.database.session import get_db
from app.models.user import User
from app.schemas.document import DocumentPublic, DocumentStatusPublic, DocumentUpdate
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=List[DocumentPublic])
def list_documents(
    q: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    starred: Optional[bool] = Query(default=None),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).list_documents(current_user, q, status, starred, sort, order)


@router.post("", response_model=DocumentPublic)
@limiter.limit(settings.UPLOAD_RATE_LIMIT)
def upload_document(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).upload(current_user, file, background)


@router.get("/{document_id}", response_model=DocumentPublic)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).get_owned(current_user, document_id)


@router.patch("/{document_id}", response_model=DocumentPublic)
def update_document(
    document_id: str,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).update(current_user, document_id, payload.name, payload.is_starred)


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    DocumentService(db).delete(current_user, document_id)
    return {"message": "Document deleted."}


@router.get("/{document_id}/status", response_model=DocumentStatusPublic)
def document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = DocumentService(db).get_owned(current_user, document_id)
    return DocumentStatusPublic(
        id=document.id,
        status=document.status,
        processing_stage=document.processing_stage,
        page_count=document.page_count,
        error_message=document.error_message,
    )


@router.get("/{document_id}/file")
def download_document(
    document_id: str,
    download: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    document = service.get_owned(current_user, document_id)
    data = service.file_bytes(current_user, document_id)
    headers = {}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{document.original_filename}"'
    mime = document.mime_type or "application/octet-stream"
    return Response(content=data, media_type=mime, headers=headers)


@router.post("/{document_id}/reprocess", response_model=DocumentPublic)
def reprocess_document(
    document_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return DocumentService(db).reprocess(current_user, document_id, background)
