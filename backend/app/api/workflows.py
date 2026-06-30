import math
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.models.workflow import WorkflowRule, WorkflowAction
from app.core.rbac import require_permission
from app.schemas.workflow import WorkflowRuleCreate, WorkflowRuleRead
from app.schemas.crm import PaginatedResponse

router = APIRouter(prefix="/crm/workflows", tags=["Workflows"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=WorkflowRuleRead, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: WorkflowRuleCreate,
    current_user: User = Depends(require_permission("accounts:read")), # Allowed for users who can read accounts
    db: Session = Depends(get_db)
):
    # Create the rule
    rule = WorkflowRule(
        name=payload.name,
        description=payload.description,
        trigger_entity=payload.trigger_entity,
        trigger_event=payload.trigger_event,
        is_active=payload.is_active
    )
    db.add(rule)
    db.flush()
    
    # Create the actions
    for idx, act in enumerate(payload.actions):
        action = WorkflowAction(
            rule_id=rule.id,
            action_type=act.action_type,
            action_params=act.action_params,
            execution_order=act.execution_order if act.execution_order else idx
        )
        db.add(action)
        
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=PaginatedResponse[WorkflowRuleRead])
def list_workflows(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    query = db.query(WorkflowRule)
    
    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(WorkflowRule.created_at.desc()).offset(offset).limit(size).all()
    
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    rule = db.query(WorkflowRule).filter(WorkflowRule.id == id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
        
    db.delete(rule)
    db.commit()
