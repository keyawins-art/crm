import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.core.rbac import require_permission
from app.models.user import User
from app.models.email import EmailLog
from app.schemas.crm import PaginatedResponse
from app.schemas.email import EmailSendRequest, EmailLogRead
from app.core.email import send_email

router = APIRouter(prefix="/crm", tags=["Emails"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/emails/send", status_code=status.HTTP_202_ACCEPTED)
def send_manual_email(
    payload: EmailSendRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("leads:create")), # Base CRM permission
):
    # Enqueue email in background so API remains fast
    background_tasks.add_task(
        send_email,
        to_email=payload.recipient,
        subject=payload.subject,
        body=payload.body,
        cc=None,
        sender_id=current_user.id,
        lead_id=payload.lead_id,
        contact_id=payload.contact_id,
        opportunity_id=payload.opportunity_id
    )
    return {"message": "Email has been queued for sending"}


@router.get("/email-logs", response_model=PaginatedResponse[EmailLogRead])
def get_email_logs(
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    lead_id: Optional[UUID] = None,
    contact_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    sender_id: Optional[UUID] = None,
    status: Optional[str] = None
):
    query = db.query(EmailLog)
    
    # Optional RLS: If Sales Exec, only see emails sent by them or to their leads/contacts?
    # Keeping it simple: Sales Executives only see emails they sent
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(EmailLog.sender_id == current_user.id)
        
    if lead_id:
        query = query.filter(EmailLog.lead_id == lead_id)
    if contact_id:
        query = query.filter(EmailLog.contact_id == contact_id)
    if opportunity_id:
        query = query.filter(EmailLog.opportunity_id == opportunity_id)
    if sender_id:
        query = query.filter(EmailLog.sender_id == sender_id)
    if status:
        query = query.filter(EmailLog.status == status)
        
    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(EmailLog.created_at.desc()).offset(offset).limit(size).all()
    
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }
