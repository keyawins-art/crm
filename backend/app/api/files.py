import os
import math
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.core.rbac import require_permission
from app.api.auth import get_current_user
from app.schemas.document import DocumentRead
from app.schemas.crm import PaginatedResponse
from app.api.crm import log_audit
from app.models.audit import AuditAction

router = APIRouter(prefix="/crm/documents", tags=["Documents Management"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", 
    ".jpg", ".jpeg", ".png", ".gif"
}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit


async def save_upload(file: UploadFile, destination: Path) -> int:
    """
    Stream-save an upload to disk, enforcing the size limit while reading.
    Returns the total number of bytes written.
    """
    size = 0
    with destination.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                output.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB",
                )
            output.write(chunk)
    return size


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    entity_type: str = Form(...),
    entity_id: UUID = Form(...),
    category: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("documents:create")),
    db: Session = Depends(get_db)
):
    # Validate extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: PDF, DOCX, Excel, Images."
        )

    # Validate entity type
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations", "tasks", "meetings", "calls", "tickets"]
    if entity_type not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid entity type")
        
    unique_filename = f"{uuid4().hex}{file_ext}"
    destination = UPLOAD_DIR / unique_filename

    # Stream-save with enforced size limit
    file_size = await save_upload(file, destination)
    
    doc = Document(
        entity_type=entity_type,
        entity_id=entity_id,
        filename=file.filename,
        file_path=unique_filename,
        content_type=file.content_type,
        file_size=file_size,
        category=category,
        uploaded_by_id=current_user.id
    )
    
    db.add(doc)
    log_audit(db, current_user, AuditAction.CREATED, "Document", entity_id)
    db.commit()
    db.refresh(doc)
    
    return doc


# ---------------------------------------------------------------------------
# Document access control
# ---------------------------------------------------------------------------
def can_read_document(user: User, doc: Document, db: Session) -> bool:
    """
    Check whether `user` may read `doc` based on the linked entity's
    ownership rules.
    """
    if not user.role:
        return False
    role_name = user.role.name.lower()

    # Admin / Sales Manager — full access
    if role_name in ("admin", "sales manager"):
        return True

    entity_id = doc.entity_id
    entity_type = doc.entity_type.lower()

    # Sales Executive — only documents attached to records they own
    if role_name == "sales executive":
        from app.models import (
            Account, Contact, Lead, Opportunity,
            Quotation, Ticket, SalesOrder,
        )

        model_map = {
            "accounts": Account,
            "contacts": Contact,
            "leads": Lead,
            "opportunities": Opportunity,
            "quotations": Quotation,
            "tickets": Ticket,
            "sales-orders": SalesOrder,
            "sales_orders": SalesOrder,
        }

        entity_model = model_map.get(entity_type)
        if not entity_model:
            return False

        entity = db.query(entity_model).filter(entity_model.id == entity_id).first()
        if not entity:
            return False

        owner_id = getattr(entity, "owner_id", None)
        assigned_to_id = getattr(entity, "assigned_to_id", None)
        assignee_id = getattr(entity, "assignee_id", None)
        created_by_id = getattr(entity, "created_by_id", None)

        return user.id in (owner_id, assigned_to_id, assignee_id, created_by_id)

    # Support — only ticket and account documents
    if role_name == "support":
        return entity_type in ("tickets", "accounts")

    # All other roles — deny by default
    return False


@router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    current_user: User = Depends(require_permission("documents:read")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Use 404 so callers cannot enumerate documents
    if not can_read_document(current_user, doc, db):
        raise HTTPException(status_code=404, detail="Document not found")

    stored_file = (UPLOAD_DIR / Path(doc.file_path).name).resolve()
    if UPLOAD_DIR.resolve() not in stored_file.parents or not stored_file.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        stored_file,
        media_type=doc.content_type or "application/octet-stream",
        filename=doc.filename,
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("", response_model=PaginatedResponse[DocumentRead])
def list_files(
    current_user: User = Depends(require_permission("documents:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    category: Optional[str] = None
):
    query = db.query(Document)
    
    if entity_type:
        query = query.filter(Document.entity_type == entity_type)
    if entity_id:
        query = query.filter(Document.entity_id == entity_id)
    if category:
        query = query.filter(Document.category == category)
        
    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(Document.created_at.desc()).offset(offset).limit(size).all()
    
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }
