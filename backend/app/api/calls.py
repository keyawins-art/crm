import math
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.core.rbac import require_permission
from app.models.user import User
from app.models.call import Call
from app.models.audit import AuditAction
from app.api.crm import log_audit  # Reuse the audit logger
from app.schemas.crm import PaginatedResponse
from app.schemas.call import CallCreate, CallRead

router = APIRouter(prefix="/crm/calls", tags=["Calls"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=CallRead, status_code=status.HTTP_201_CREATED)
def create_call(
    payload: CallCreate,
    current_user: User = Depends(require_permission("leads:create")), # Base CRM permission
    db: Session = Depends(get_db),
):
    obj = Call(**payload.model_dump(exclude_none=True))
    
    obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, "Call", obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=PaginatedResponse[CallRead])
def list_calls(
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    lead_id: Optional[UUID] = None,
    contact_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None
):
    query = db.query(Call).filter(Call.is_deleted == False)

    # RLS Enforcement: Sales Executives see only calls logged by them
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(Call.created_by_id == current_user.id)

    # Filters
    if lead_id:
        query = query.filter(Call.lead_id == lead_id)
    if contact_id:
        query = query.filter(Call.contact_id == contact_id)
    if opportunity_id:
        query = query.filter(Call.opportunity_id == opportunity_id)

    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(Call.created_at.desc()).offset(offset).limit(size).all()

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }
