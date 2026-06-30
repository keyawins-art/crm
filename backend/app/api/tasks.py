import math
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.core.rbac import require_permission
from app.models.user import User
from app.models.task import Task
from app.models.audit import AuditAction
from app.api.crm import log_audit  # Reuse the audit logger
from app.schemas.crm import PaginatedResponse
from app.schemas.task import TaskCreate, TaskUpdate, TaskRead

router = APIRouter(prefix="/crm/tasks", tags=["Tasks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: User = Depends(require_permission("leads:create")), # Using basic permission for now, or you can add "tasks:create"
    db: Session = Depends(get_db),
):
    obj = Task(**payload.model_dump(exclude_none=True))
    
    # Auto-assign
    if not obj.assigned_to_id:
        obj.assigned_to_id = current_user.id
    obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, "Task", obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=PaginatedResponse[TaskRead])
def list_tasks(
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    assigned_to_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    contact_id: Optional[UUID] = None,
    opportunity_id: Optional[UUID] = None,
    status: Optional[str] = None
):
    query = db.query(Task).filter(Task.is_deleted == False)

    # RLS Enforcement: Sales Executives see only tasks assigned to them or created by them
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Task.assigned_to_id == current_user.id, Task.created_by_id == current_user.id))

    # Filters
    if assigned_to_id:
        query = query.filter(Task.assigned_to_id == assigned_to_id)
    if lead_id:
        query = query.filter(Task.lead_id == lead_id)
    if contact_id:
        query = query.filter(Task.contact_id == contact_id)
    if opportunity_id:
        query = query.filter(Task.opportunity_id == opportunity_id)
    if status:
        query = query.filter(Task.status == status)

    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(Task.due_date.asc().nulls_last()).offset(offset).limit(size).all()

    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/{id}", response_model=TaskRead)
def get_task(
    id: UUID,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.id == id, Task.is_deleted == False)

    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Task.assigned_to_id == current_user.id, Task.created_by_id == current_user.id))

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    log_audit(db, current_user, AuditAction.VIEWED, "Task", obj.id)
    db.commit()
    return obj


@router.put("/{id}", response_model=TaskRead)
def update_task(
    id: UUID,
    payload: TaskUpdate,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.id == id, Task.is_deleted == False)

    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Task.assigned_to_id == current_user.id, Task.created_by_id == current_user.id))

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, "Task", obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: UUID,
    current_user: User = Depends(require_permission("leads:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    
    query = db.query(Task).filter(Task.id == id, Task.is_deleted == False)

    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(or_(Task.assigned_to_id == current_user.id, Task.created_by_id == current_user.id))

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")
    
    obj.is_deleted = True
    obj.deleted_at = func.now()
    
    log_audit(db, current_user, AuditAction.DELETED, "Task", obj.id)
    db.commit()
