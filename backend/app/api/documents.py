import os
import math
from uuid import UUID, uuid4
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.core.rbac import require_permission
from app.schemas.document import DocumentRead
from app.schemas.crm import PaginatedResponse
from app.api.crm import log_audit
from app.models.audit import AuditAction
from app.api.files import save_upload, UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE

router = APIRouter(prefix="/crm", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{module_name}/{id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    module_name: str,
    id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("documents:create")),
    db: Session = Depends(get_db)
):
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations", "tickets"]
    if module_name not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid module name")

    # Validate extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Supported formats: PDF, DOCX, Excel, Images.",
        )
    
    # Generate unique filename to prevent collisions
    unique_filename = f"{uuid4().hex}{file_ext}"
    destination = UPLOAD_DIR / unique_filename

    # Stream-save with enforced size limit
    file_size = await save_upload(file, destination)
    
    doc = Document(
        entity_type=module_name,
        entity_id=id,
        filename=file.filename,
        file_path=unique_filename,
        content_type=file.content_type,
        file_size=file_size,
        uploaded_by_id=current_user.id
    )
    
    db.add(doc)
    log_audit(db, current_user, AuditAction.CREATED, "Document", id)
    db.commit()
    db.refresh(doc)
    
    return doc


@router.get("/{module_name}/{id}/documents", response_model=PaginatedResponse[DocumentRead])
def list_documents(
    module_name: str,
    id: UUID,
    current_user: User = Depends(require_permission("documents:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    query = db.query(Document).filter(
        Document.entity_type == module_name,
        Document.entity_id == id
    )
    
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


@router.delete("/documents/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    id: UUID,
    current_user: User = Depends(require_permission("documents:delete")),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Remove file from disk safely
    stored_file = (UPLOAD_DIR / Path(doc.file_path).name).resolve()
    if UPLOAD_DIR.resolve() in stored_file.parents and stored_file.is_file():
        stored_file.unlink()
        
    db.delete(doc)
    log_audit(db, current_user, AuditAction.DELETED, "Document", doc.entity_id)
    db.commit()
