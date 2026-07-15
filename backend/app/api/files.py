import os
import shutil
import math
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.core.rbac import require_permission
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

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", 
    ".jpg", ".jpeg", ".png", ".gif"
}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit

@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_file(
    entity_type: str = Form(...),
    entity_id: UUID = Form(...),
    category: Optional[str] = Form(None), # e.g. "Customer Documents", "GST Certificate", etc.
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("accounts:update")),
    db: Session = Depends(get_db)
):
    # Validate extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Supported formats: PDF, DOCX, Excel, Images."
        )

    # Validate file size
    if file.size and file.size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB."
        )

    # Validate entity
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations", "tasks", "meetings", "calls"]
    if entity_type not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid entity type")
        
    unique_filename = f"{uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = os.path.getsize(file_path)
    
    doc = Document(
        entity_type=entity_type,
        entity_id=entity_id,
        filename=file.filename,
        file_path=file_path,
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


@router.get("", response_model=PaginatedResponse[DocumentRead])
def list_files(
    current_user: User = Depends(require_permission("accounts:read")),
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
