import os
import shutil
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.core.rbac import require_permission
from app.schemas.document import DocumentRead
from app.schemas.crm import PaginatedResponse
from app.api.crm import log_audit
from app.models.audit import AuditAction

router = APIRouter(prefix="/crm", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIR = "uploads"

@router.post("/{module_name}/{id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    module_name: str,
    id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("accounts:update")),
    db: Session = Depends(get_db)
):
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations"]
    if module_name not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid module name")
    
    # Generate unique filename to prevent collisions
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    
    doc = Document(
        entity_type=module_name,
        entity_id=id,
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
        file_size=file_size,
        uploaded_by_id=current_user.id
    )
    
    db.add(doc)
    
    # Audit log
    log_audit(db, current_user, AuditAction.CREATED, "Document", id)
    
    db.commit()
    db.refresh(doc)
    
    return doc


@router.get("/{module_name}/{id}/documents", response_model=PaginatedResponse[DocumentRead])
def list_documents(
    module_name: str,
    id: UUID,
    current_user: User = Depends(require_permission("accounts:read")),
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
    
    import math
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
    current_user: User = Depends(require_permission("accounts:delete")),
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Remove file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        
    db.delete(doc)
    log_audit(db, current_user, AuditAction.DELETED, "Document", doc.entity_id)
    db.commit()
