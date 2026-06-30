import math
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.core.rbac import require_permission
from app.models.user import User
from app.models.meeting import Meeting
from app.models.audit import AuditAction
from app.api.crm import log_audit  # Reuse the audit logger
from app.schemas.crm import PaginatedResponse
from app.schemas.meeting import MeetingCreate, MeetingRead

router = APIRouter(prefix="/crm/meetings", tags=["Meetings"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
def create_meeting(
    payload: MeetingCreate,
    current_user: User = Depends(require_permission("leads:create")), # Base CRM permission
    db: Session = Depends(get_db),
):
    obj = Meeting(**payload.model_dump(exclude_none=True))
    
    obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, "Meeting", obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=PaginatedResponse[MeetingRead])
def list_meetings(
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    lead_id: Optional[UUID] = None,
    contact_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    status: Optional[str] = None
):
    query = db.query(Meeting).filter(Meeting.is_deleted == False)

    # RLS Enforcement: Sales Executives see only meetings created by them 
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(Meeting.created_by_id == current_user.id)

    # Filters
    if lead_id:
        query = query.filter(Meeting.lead_id == lead_id)
    if contact_id:
        query = query.filter(Meeting.contact_id == contact_id)
    if opportunity_id:
        query = query.filter(Meeting.opportunity_id == opportunity_id)
    if status:
        query = query.filter(Meeting.status == status)

    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(Meeting.start_time.asc()).offset(offset).limit(size).all()

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }
