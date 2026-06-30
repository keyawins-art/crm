import math
import random
from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.models.user import User
from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketComment
from app.models.audit import AuditAction
from app.api.crm import log_audit  # Reuse audit logs
from app.core.rbac import require_permission

from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate, TicketCommentCreate, TicketCommentRead
from app.schemas.crm import PaginatedResponse

router = APIRouter(prefix="/crm/tickets", tags=["Customer Support"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_ticket_number() -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    rand_val = random.randint(1000, 9999)
    return f"TKT-{date_str}-{rand_val}"


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(require_permission("tickets:create")),
    db: Session = Depends(get_db)
):
    """Create a new customer support ticket."""
    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        subject=payload.subject,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        account_id=payload.account_id,
        contact_id=payload.contact_id,
        assigned_to_id=payload.assigned_to_id,
        created_by_id=current_user.id
    )
    
    # Auto-assign if not provided
    if not ticket.assigned_to_id:
        ticket.assigned_to_id = current_user.id
        
    db.add(ticket)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, "Ticket", ticket.id)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=PaginatedResponse[TicketRead])
def list_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    current_user: User = Depends(require_permission("tickets:read")),
    db: Session = Depends(get_db)
):
    """List customer support tickets with RLS."""
    query = db.query(Ticket).filter(Ticket.is_deleted == False)
    
    # RLS Enforcement: Sales Executives only see tickets assigned to them or created by them
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Ticket.assigned_to_id == current_user.id, Ticket.created_by_id == current_user.id))
        
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
        
    total = query.count()
    items = query.order_by(Ticket.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/{id}", response_model=TicketRead)
def get_ticket(
    id: UUID,
    current_user: User = Depends(require_permission("tickets:read")),
    db: Session = Depends(get_db)
):
    """Get support ticket details."""
    query = db.query(Ticket).filter(Ticket.id == id, Ticket.is_deleted == False)
    
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Ticket.assigned_to_id == current_user.id, Ticket.created_by_id == current_user.id))
        
    ticket = query.first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    return ticket


@router.put("/{id}", response_model=TicketRead)
def update_ticket(
    id: UUID,
    payload: TicketUpdate,
    current_user: User = Depends(require_permission("tickets:update")),
    db: Session = Depends(get_db)
):
    """Update support ticket status, priority, or details."""
    query = db.query(Ticket).filter(Ticket.id == id, Ticket.is_deleted == False)
    
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Ticket.assigned_to_id == current_user.id, Ticket.created_by_id == current_user.id))
        
    ticket = query.first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, "Ticket", ticket.id)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    id: UUID,
    current_user: User = Depends(require_permission("tickets:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete a support ticket."""
    query = db.query(Ticket).filter(Ticket.id == id, Ticket.is_deleted == False)
    
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Ticket.assigned_to_id == current_user.id, Ticket.created_by_id == current_user.id))
        
    ticket = query.first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    ticket.is_deleted = True
    ticket.deleted_at = datetime.now(timezone.utc)
    
    log_audit(db, current_user, AuditAction.DELETED, "Ticket", ticket.id)
    db.commit()


@router.post("/{id}/comments", response_model=TicketCommentRead, status_code=status.HTTP_201_CREATED)
def add_ticket_comment(
    id: UUID,
    payload: TicketCommentCreate,
    current_user: User = Depends(require_permission("tickets:update")),
    db: Session = Depends(get_db)
):
    """Add a comment or internal note to a support ticket."""
    query = db.query(Ticket).filter(Ticket.id == id, Ticket.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Ticket.assigned_to_id == current_user.id, Ticket.created_by_id == current_user.id))
        
    ticket = query.first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        content=payload.content,
        is_internal=payload.is_internal
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{id}/comments", response_model=List[TicketCommentRead])
def list_ticket_comments(
    id: UUID,
    current_user: User = Depends(require_permission("tickets:read")),
    db: Session = Depends(get_db)
):
    """List comments on a support ticket."""
    query = db.query(Ticket).filter(Ticket.id == id, Ticket.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Ticket.assigned_to_id == current_user.id, Ticket.created_by_id == current_user.id))
        
    ticket = query.first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    comments_query = db.query(TicketComment).filter(TicketComment.ticket_id == ticket.id, TicketComment.is_deleted == False)
    
    # Optionally restrict internal notes from customers (if a Customer role exists in the future)
    # For now, sales execs and admins can see internal notes.
    
    return comments_query.order_by(TicketComment.created_at.asc()).all()
