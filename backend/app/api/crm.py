from app.schemas.activity import ActivityRead
from app.api.notifications import send_notification
from app.models.audit import NotificationType
from app.schemas.activity import ActivityCreate, ActivityRead
from datetime import date, timedelta
import math
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.core.rbac import require_permission
from app.core.email import send_email
from app.core.workflow import execute_workflows
from app.models.lead import LeadStatus, LeadNote, LeadActivity
from app.models.opportunity import OpportunityStage
from app.models.audit import AuditLog, AuditAction
from app.models.activity import TimelineActivity
from app.models import (
    Account,
    Contact,
    Lead,
    Opportunity,
    Product,
    Quotation,
    User,
)
from app.schemas.crm import (
    AccountCreate, AccountRead, AccountUpdate,
    ContactCreate, ContactRead, ContactUpdate,
    LeadCreate, LeadRead, LeadUpdate, LeadConvert, LeadConversionResponse, LeadNoteCreate, LeadNoteRead, LeadActivityCreate, LeadActivityRead, DashboardRead, KPIRead, MonthlyLeadChart, RevenueChart, FunnelChart, AuditLogRead,
    OpportunityCreate, OpportunityRead, OpportunityUpdate,
    ProductCreate, ProductRead, ProductUpdate,
    QuotationCreate, QuotationRead, QuotationUpdate,
    UserCreate, UserRead, PaginatedResponse
)

router = APIRouter(prefix="/crm", tags=["CRM"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



def log_audit(db: Session, user: User, action: AuditAction, entity_type: str, entity_id: UUID):
    user_name = user.first_name or "User"
    action_str = "created" if action == AuditAction.CREATED else "updated" if action == AuditAction.UPDATED else "deleted"
    message = f"{user_name} {action_str} {entity_type}"
    
    audit_log = AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=message
    )
    db.add(audit_log)
    # We do NOT commit here, we rely on the caller's transaction


@router.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}






# Accounts
@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("accounts:create")),
    db: Session = Depends(get_db),
):
    obj = Account(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    if obj.email:
        background_tasks.add_task(
            send_email,
            obj.email,
            "Welcome to our CRM!",
            f"Hi {obj.first_name},\n\nThank you for connecting with us. We will follow up shortly.\n\nBest regards,\nSales Team"
        )
    return obj


@router.get("/accounts", response_model=PaginatedResponse[AccountRead])
def list_accounts(
    request: Request,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_deleted: bool = False,
    search: Optional[str] = None,
    industry: Optional[str] = None,
    type: Optional[str] = None,
):
    query = db.query(Account)
    if not include_deleted:
        query = query.filter(Account.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            query = query.filter(Account.owner_id == current_user.id)
        elif hasattr(Account, 'assigned_to_id'):
            if hasattr(Account, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Account.assigned_to_id == current_user.id, Account.created_by_id == current_user.id))
            else:
                query = query.filter(Account.assigned_to_id == current_user.id)
        elif hasattr(Account, 'created_by_id'):
            query = query.filter(Account.created_by_id == current_user.id)

    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Account, field):
                search_filters.append(getattr(Account, field).ilike(f"%{search}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    # Dynamic Field Filtering
    known_params = {"page", "size", "sort", "order", "include_deleted", "search"}
    for key, value in request.query_params.items():
        if key not in known_params and hasattr(Account, key):
            query = query.filter(getattr(Account, key) == value)

    # Sorting
    if sort and hasattr(Account, sort):
        sort_attr = getattr(Account, sort)
        if order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
    else:
        # Default sort by created_at if it exists
        if hasattr(Account, 'created_at'):
            if order == "desc":
                query = query.order_by(Account.created_at.desc())
            else:
                query = query.order_by(Account.created_at.asc())

    total = query.count()
    offset = (page - 1) * size
    
    items = query.offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/accounts/{id}", response_model=AccountRead)
def get_account(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Account).filter(Account.id == id, Account.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            query = query.filter(Account.owner_id == current_user.id)
        elif hasattr(Account, 'assigned_to_id'):
            if hasattr(Account, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Account.assigned_to_id == current_user.id, Account.created_by_id == current_user.id))
            else:
                query = query.filter(Account.assigned_to_id == current_user.id)
        elif hasattr(Account, 'created_by_id'):
            query = query.filter(Account.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
    return obj


@router.put("/accounts/{id}", response_model=AccountRead)
def update_account(
    id: UUID,
    payload: AccountUpdate,
    current_user: User = Depends(require_permission("accounts:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Account).filter(Account.id == id, Account.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            query = query.filter(Account.owner_id == current_user.id)
        elif hasattr(Account, 'assigned_to_id'):
            if hasattr(Account, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Account.assigned_to_id == current_user.id, Account.created_by_id == current_user.id))
            else:
                query = query.filter(Account.assigned_to_id == current_user.id)
        elif hasattr(Account, 'created_by_id'):
            query = query.filter(Account.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    if 'status' in update_data and str(update_data['status']).lower() == 'sent' and obj.opportunity and obj.opportunity.contact and obj.opportunity.contact.email:
        background_tasks.add_task(
            send_email,
            obj.opportunity.contact.email,
            f"Quotation {getattr(obj, 'quote_number', 'unknown')} Attached",
            f"Hi {obj.opportunity.contact.first_name},\n\nPlease find the attached quotation for {obj.opportunity.name}.\n\nTotal Amount: {obj.total_amount}\n\nBest regards,\nSales Team"
        )
    return obj


@router.delete("/accounts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query(Account).filter(Account.id == id, Account.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            query = query.filter(Account.owner_id == current_user.id)
        elif hasattr(Account, 'assigned_to_id'):
            if hasattr(Account, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Account.assigned_to_id == current_user.id, Account.created_by_id == current_user.id))
            else:
                query = query.filter(Account.assigned_to_id == current_user.id)
        elif hasattr(Account, 'created_by_id'):
            query = query.filter(Account.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.delete("/accounts/{id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_account(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:delete")),
    db: Session = Depends(get_db),
):
    query = db.query(Account).filter(Account.id == id)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            query = query.filter(Account.owner_id == current_user.id)
        elif hasattr(Account, 'assigned_to_id'):
            if hasattr(Account, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Account.assigned_to_id == current_user.id, Account.created_by_id == current_user.id))
            else:
                query = query.filter(Account.assigned_to_id == current_user.id)
        elif hasattr(Account, 'created_by_id'):
            query = query.filter(Account.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found")
        
    db.delete(obj)
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.post("/accounts/{id}/restore", response_model=AccountRead)
def restore_account(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Account).filter(Account.id == id, Account.is_deleted == True)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            query = query.filter(Account.owner_id == current_user.id)
        elif hasattr(Account, 'assigned_to_id'):
            if hasattr(Account, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Account.assigned_to_id == current_user.id, Account.created_by_id == current_user.id))
            else:
                query = query.filter(Account.assigned_to_id == current_user.id)
        elif hasattr(Account, 'created_by_id'):
            query = query.filter(Account.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Account not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


# Contacts
@router.post("/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    current_user: User = Depends(require_permission("contacts:create")),
    db: Session = Depends(get_db),
):
    if payload.email and db.query(Contact).filter(Contact.email == payload.email, Contact.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="Contact with this email already exists")
    obj = Contact(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit() # secondary commit for audit if needed, but actually we should log before commit.
    db.refresh(obj)
    return obj


@router.get("/contacts", response_model=PaginatedResponse[ContactRead])
def list_contacts(
    request: Request,
    current_user: User = Depends(require_permission("contacts:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_deleted: bool = False,
    search: Optional[str] = None,
):
    query = db.query(Contact)
    if not include_deleted:
        query = query.filter(Contact.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            query = query.filter(Contact.owner_id == current_user.id)
        elif hasattr(Contact, 'assigned_to_id'):
            if hasattr(Contact, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Contact.assigned_to_id == current_user.id, Contact.created_by_id == current_user.id))
            else:
                query = query.filter(Contact.assigned_to_id == current_user.id)
        elif hasattr(Contact, 'created_by_id'):
            query = query.filter(Contact.created_by_id == current_user.id)

    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Contact, field):
                search_filters.append(getattr(Contact, field).ilike(f"%{search}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    # Dynamic Field Filtering
    known_params = {"page", "size", "sort", "order", "include_deleted", "search"}
    for key, value in request.query_params.items():
        if key not in known_params and hasattr(Contact, key):
            query = query.filter(getattr(Contact, key) == value)

    # Sorting
    if sort and hasattr(Contact, sort):
        sort_attr = getattr(Contact, sort)
        if order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
    else:
        # Default sort by created_at if it exists
        if hasattr(Contact, 'created_at'):
            if order == "desc":
                query = query.order_by(Contact.created_at.desc())
            else:
                query = query.order_by(Contact.created_at.asc())

    total = query.count()
    offset = (page - 1) * size
    
    items = query.offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/contacts/{id}", response_model=ContactRead)
def get_contact(
    id: UUID,
    current_user: User = Depends(require_permission("contacts:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).filter(Contact.id == id, Contact.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            query = query.filter(Contact.owner_id == current_user.id)
        elif hasattr(Contact, 'assigned_to_id'):
            if hasattr(Contact, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Contact.assigned_to_id == current_user.id, Contact.created_by_id == current_user.id))
            else:
                query = query.filter(Contact.assigned_to_id == current_user.id)
        elif hasattr(Contact, 'created_by_id'):
            query = query.filter(Contact.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    return obj


@router.put("/contacts/{id}", response_model=ContactRead)
def update_contact(
    id: UUID,
    payload: ContactUpdate,
    current_user: User = Depends(require_permission("contacts:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).filter(Contact.id == id, Contact.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            query = query.filter(Contact.owner_id == current_user.id)
        elif hasattr(Contact, 'assigned_to_id'):
            if hasattr(Contact, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Contact.assigned_to_id == current_user.id, Contact.created_by_id == current_user.id))
            else:
                query = query.filter(Contact.assigned_to_id == current_user.id)
        elif hasattr(Contact, 'created_by_id'):
            query = query.filter(Contact.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/contacts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(
    id: UUID,
    current_user: User = Depends(require_permission("contacts:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query(Contact).filter(Contact.id == id, Contact.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            query = query.filter(Contact.owner_id == current_user.id)
        elif hasattr(Contact, 'assigned_to_id'):
            if hasattr(Contact, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Contact.assigned_to_id == current_user.id, Contact.created_by_id == current_user.id))
            else:
                query = query.filter(Contact.assigned_to_id == current_user.id)
        elif hasattr(Contact, 'created_by_id'):
            query = query.filter(Contact.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.delete("/contacts/{id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_contact(
    id: UUID,
    current_user: User = Depends(require_permission("contacts:delete")),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).filter(Contact.id == id)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            query = query.filter(Contact.owner_id == current_user.id)
        elif hasattr(Contact, 'assigned_to_id'):
            if hasattr(Contact, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Contact.assigned_to_id == current_user.id, Contact.created_by_id == current_user.id))
            else:
                query = query.filter(Contact.assigned_to_id == current_user.id)
        elif hasattr(Contact, 'created_by_id'):
            query = query.filter(Contact.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found")
        
    db.delete(obj)
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.post("/contacts/{id}/restore", response_model=ContactRead)
def restore_contact(
    id: UUID,
    current_user: User = Depends(require_permission("contacts:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Contact).filter(Contact.id == id, Contact.is_deleted == True)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            query = query.filter(Contact.owner_id == current_user.id)
        elif hasattr(Contact, 'assigned_to_id'):
            if hasattr(Contact, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Contact.assigned_to_id == current_user.id, Contact.created_by_id == current_user.id))
            else:
                query = query.filter(Contact.assigned_to_id == current_user.id)
        elif hasattr(Contact, 'created_by_id'):
            query = query.filter(Contact.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Contact not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


# Leads
@router.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("leads:create")),
    db: Session = Depends(get_db),
):
    if payload.email and db.query(Lead).filter(Lead.email == payload.email, Lead.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="Lead with this email already exists")
    obj = Lead(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit() # secondary commit for audit if needed, but actually we should log before commit.
    
    if hasattr(obj, 'assigned_to_id') and obj.assigned_to_id and obj.assigned_to_id != current_user.id:
        send_notification(
            db=db,
            user_id=obj.assigned_to_id,
            title="Lead Assigned",
            message=f"You have been assigned a new lead: {obj.first_name} {obj.last_name}",
            type=NotificationType.INFO
        )

    # Trigger Workflows
    background_tasks.add_task(execute_workflows, "Lead", "created", obj.id, current_user.id)

    db.refresh(obj)
    return obj


@router.get("/leads", response_model=PaginatedResponse[LeadRead])
def list_leads(
    request: Request,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_deleted: bool = False,
    search: Optional[str] = None,
):
    query = db.query(Lead)
    if not include_deleted:
        query = query.filter(Lead.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Lead, field):
                search_filters.append(getattr(Lead, field).ilike(f"%{search}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    # Dynamic Field Filtering
    known_params = {"page", "size", "sort", "order", "include_deleted", "search"}
    for key, value in request.query_params.items():
        if key not in known_params and hasattr(Lead, key):
            query = query.filter(getattr(Lead, key) == value)

    # Sorting
    if sort and hasattr(Lead, sort):
        sort_attr = getattr(Lead, sort)
        if order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
    else:
        # Default sort by created_at if it exists
        if hasattr(Lead, 'created_at'):
            if order == "desc":
                query = query.order_by(Lead.created_at.desc())
            else:
                query = query.order_by(Lead.created_at.asc())

    total = query.count()
    offset = (page - 1) * size
    
    items = query.offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/leads/{id}", response_model=LeadRead)
def get_lead(
    id: UUID,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
    return obj


@router.put("/leads/{id}", response_model=LeadRead)
def update_lead(
    id: UUID,
    payload: LeadUpdate,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    if 'assigned_to_id' in update_data and update_data['assigned_to_id'] and update_data['assigned_to_id'] != current_user.id:
        send_notification(
            db=db,
            user_id=update_data['assigned_to_id'],
            title="Lead Assigned",
            message=f"You have been assigned a lead: {obj.first_name} {obj.last_name}",
            type=NotificationType.INFO
        )
        
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/leads/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    id: UUID,
    current_user: User = Depends(require_permission("leads:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.delete("/leads/{id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_lead(
    id: UUID,
    current_user: User = Depends(require_permission("leads:delete")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    db.delete(obj)
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.post("/leads/{id}/restore", response_model=LeadRead)
def restore_lead(
    id: UUID,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == True)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lead not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


# Products
@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(require_permission("products:create")),
    db: Session = Depends(get_db),
):
    obj = Product(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit() # secondary commit for audit if needed, but actually we should log before commit.
    db.refresh(obj)
    return obj


@router.get("/products", response_model=PaginatedResponse[ProductRead])
def list_products(
    request: Request,
    current_user: User = Depends(require_permission("products:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_deleted: bool = False,
    search: Optional[str] = None,
):
    query = db.query(Product)
    if not include_deleted:
        query = query.filter(Product.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Product, 'owner_id'):
            query = query.filter(Product.owner_id == current_user.id)
        elif hasattr(Product, 'assigned_to_id'):
            if hasattr(Product, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Product.assigned_to_id == current_user.id, Product.created_by_id == current_user.id))
            else:
                query = query.filter(Product.assigned_to_id == current_user.id)
        elif hasattr(Product, 'created_by_id'):
            query = query.filter(Product.created_by_id == current_user.id)

    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Product, field):
                search_filters.append(getattr(Product, field).ilike(f"%{search}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    # Dynamic Field Filtering
    known_params = {"page", "size", "sort", "order", "include_deleted", "search"}
    for key, value in request.query_params.items():
        if key not in known_params and hasattr(Product, key):
            query = query.filter(getattr(Product, key) == value)

    # Sorting
    if sort and hasattr(Product, sort):
        sort_attr = getattr(Product, sort)
        if order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
    else:
        # Default sort by created_at if it exists
        if hasattr(Product, 'created_at'):
            if order == "desc":
                query = query.order_by(Product.created_at.desc())
            else:
                query = query.order_by(Product.created_at.asc())

    total = query.count()
    offset = (page - 1) * size
    
    items = query.offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/products/{id}", response_model=ProductRead)
def get_product(
    id: UUID,
    current_user: User = Depends(require_permission("products:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.id == id, Product.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Product, 'owner_id'):
            query = query.filter(Product.owner_id == current_user.id)
        elif hasattr(Product, 'assigned_to_id'):
            if hasattr(Product, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Product.assigned_to_id == current_user.id, Product.created_by_id == current_user.id))
            else:
                query = query.filter(Product.assigned_to_id == current_user.id)
        elif hasattr(Product, 'created_by_id'):
            query = query.filter(Product.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj


@router.put("/products/{id}", response_model=ProductRead)
def update_product(
    id: UUID,
    payload: ProductUpdate,
    current_user: User = Depends(require_permission("products:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.id == id, Product.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Product, 'owner_id'):
            query = query.filter(Product.owner_id == current_user.id)
        elif hasattr(Product, 'assigned_to_id'):
            if hasattr(Product, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Product.assigned_to_id == current_user.id, Product.created_by_id == current_user.id))
            else:
                query = query.filter(Product.assigned_to_id == current_user.id)
        elif hasattr(Product, 'created_by_id'):
            query = query.filter(Product.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/products/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    id: UUID,
    current_user: User = Depends(require_permission("products:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query(Product).filter(Product.id == id, Product.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Product, 'owner_id'):
            query = query.filter(Product.owner_id == current_user.id)
        elif hasattr(Product, 'assigned_to_id'):
            if hasattr(Product, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Product.assigned_to_id == current_user.id, Product.created_by_id == current_user.id))
            else:
                query = query.filter(Product.assigned_to_id == current_user.id)
        elif hasattr(Product, 'created_by_id'):
            query = query.filter(Product.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.delete("/products/{id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_product(
    id: UUID,
    current_user: User = Depends(require_permission("products:delete")),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.id == id)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Product, 'owner_id'):
            query = query.filter(Product.owner_id == current_user.id)
        elif hasattr(Product, 'assigned_to_id'):
            if hasattr(Product, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Product.assigned_to_id == current_user.id, Product.created_by_id == current_user.id))
            else:
                query = query.filter(Product.assigned_to_id == current_user.id)
        elif hasattr(Product, 'created_by_id'):
            query = query.filter(Product.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db.delete(obj)
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.post("/products/{id}/restore", response_model=ProductRead)
def restore_product(
    id: UUID,
    current_user: User = Depends(require_permission("products:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.id == id, Product.is_deleted == True)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Product, 'owner_id'):
            query = query.filter(Product.owner_id == current_user.id)
        elif hasattr(Product, 'assigned_to_id'):
            if hasattr(Product, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Product.assigned_to_id == current_user.id, Product.created_by_id == current_user.id))
            else:
                query = query.filter(Product.assigned_to_id == current_user.id)
        elif hasattr(Product, 'created_by_id'):
            query = query.filter(Product.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


# Opportunities
@router.post("/opportunities", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunitie(
    payload: OpportunityCreate,
    current_user: User = Depends(require_permission("opportunities:create")),
    db: Session = Depends(get_db),
):
    obj = Opportunity(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit() # secondary commit for audit if needed, but actually we should log before commit.
    db.refresh(obj)
    return obj


@router.get("/opportunities", response_model=PaginatedResponse[OpportunityRead])
def list_opportunities(
    request: Request,
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_deleted: bool = False,
    search: Optional[str] = None,
):
    query = db.query(Opportunity)
    if not include_deleted:
        query = query.filter(Opportunity.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'owner_id'):
            query = query.filter(Opportunity.owner_id == current_user.id)
        elif hasattr(Opportunity, 'assigned_to_id'):
            if hasattr(Opportunity, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Opportunity.assigned_to_id == current_user.id, Opportunity.created_by_id == current_user.id))
            else:
                query = query.filter(Opportunity.assigned_to_id == current_user.id)
        elif hasattr(Opportunity, 'created_by_id'):
            query = query.filter(Opportunity.created_by_id == current_user.id)

    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Opportunity, field):
                search_filters.append(getattr(Opportunity, field).ilike(f"%{search}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    # Dynamic Field Filtering
    known_params = {"page", "size", "sort", "order", "include_deleted", "search"}
    for key, value in request.query_params.items():
        if key not in known_params and hasattr(Opportunity, key):
            query = query.filter(getattr(Opportunity, key) == value)

    # Sorting
    if sort and hasattr(Opportunity, sort):
        sort_attr = getattr(Opportunity, sort)
        if order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
    else:
        # Default sort by created_at if it exists
        if hasattr(Opportunity, 'created_at'):
            if order == "desc":
                query = query.order_by(Opportunity.created_at.desc())
            else:
                query = query.order_by(Opportunity.created_at.asc())

    total = query.count()
    offset = (page - 1) * size
    
    items = query.offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/opportunities/{id}", response_model=OpportunityRead)
def get_opportunitie(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).filter(Opportunity.id == id, Opportunity.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'owner_id'):
            query = query.filter(Opportunity.owner_id == current_user.id)
        elif hasattr(Opportunity, 'assigned_to_id'):
            if hasattr(Opportunity, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Opportunity.assigned_to_id == current_user.id, Opportunity.created_by_id == current_user.id))
            else:
                query = query.filter(Opportunity.assigned_to_id == current_user.id)
        elif hasattr(Opportunity, 'created_by_id'):
            query = query.filter(Opportunity.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return obj


@router.put("/opportunities/{id}", response_model=OpportunityRead)
def update_opportunitie(
    id: UUID,
    payload: OpportunityUpdate,
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).filter(Opportunity.id == id, Opportunity.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'owner_id'):
            query = query.filter(Opportunity.owner_id == current_user.id)
        elif hasattr(Opportunity, 'assigned_to_id'):
            if hasattr(Opportunity, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Opportunity.assigned_to_id == current_user.id, Opportunity.created_by_id == current_user.id))
            else:
                query = query.filter(Opportunity.assigned_to_id == current_user.id)
        elif hasattr(Opportunity, 'created_by_id'):
            query = query.filter(Opportunity.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/opportunities/{id}/pay", response_model=OpportunityRead)
def mark_opportunity_paid(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db),
):
    """Mock endpoint to record a payment and trigger a notification."""
    obj = db.query(Opportunity).filter(Opportunity.id == id, Opportunity.is_deleted == False).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    obj.stage = OpportunityStage.CLOSED_WON
    log_audit(db, current_user, AuditAction.UPDATED, "Opportunity (Payment)", obj.id)
    
    # Send Notification to Opportunity Owner
    owner_id = getattr(obj, 'assigned_to_id', getattr(obj, 'owner_id', current_user.id))
    send_notification(
        db=db,
        user_id=owner_id,
        title="Payment Received",
        message=f"Payment received for Opportunity: {obj.name}. Status updated to Closed Won.",
        type=NotificationType.SUCCESS
    )
    
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/opportunities/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunitie(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query(Opportunity).filter(Opportunity.id == id, Opportunity.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'owner_id'):
            query = query.filter(Opportunity.owner_id == current_user.id)
        elif hasattr(Opportunity, 'assigned_to_id'):
            if hasattr(Opportunity, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Opportunity.assigned_to_id == current_user.id, Opportunity.created_by_id == current_user.id))
            else:
                query = query.filter(Opportunity.assigned_to_id == current_user.id)
        elif hasattr(Opportunity, 'created_by_id'):
            query = query.filter(Opportunity.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.delete("/opportunities/{id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_opportunitie(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:delete")),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).filter(Opportunity.id == id)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'owner_id'):
            query = query.filter(Opportunity.owner_id == current_user.id)
        elif hasattr(Opportunity, 'assigned_to_id'):
            if hasattr(Opportunity, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Opportunity.assigned_to_id == current_user.id, Opportunity.created_by_id == current_user.id))
            else:
                query = query.filter(Opportunity.assigned_to_id == current_user.id)
        elif hasattr(Opportunity, 'created_by_id'):
            query = query.filter(Opportunity.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    db.delete(obj)
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.post("/opportunities/{id}/restore", response_model=OpportunityRead)
def restore_opportunitie(
    id: UUID,
    current_user: User = Depends(require_permission("opportunities:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Opportunity).filter(Opportunity.id == id, Opportunity.is_deleted == True)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'owner_id'):
            query = query.filter(Opportunity.owner_id == current_user.id)
        elif hasattr(Opportunity, 'assigned_to_id'):
            if hasattr(Opportunity, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Opportunity.assigned_to_id == current_user.id, Opportunity.created_by_id == current_user.id))
            else:
                query = query.filter(Opportunity.assigned_to_id == current_user.id)
        elif hasattr(Opportunity, 'created_by_id'):
            query = query.filter(Opportunity.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Opportunity not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


# Quotations
@router.post("/quotations", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    current_user: User = Depends(require_permission("quotations:create")),
    db: Session = Depends(get_db),
):
    obj = Quotation(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.flush()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit()
    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)
    db.commit() # secondary commit for audit if needed, but actually we should log before commit.
    db.refresh(obj)
    return obj


@router.get("/quotations", response_model=PaginatedResponse[QuotationRead])
def list_quotations(
    request: Request,
    current_user: User = Depends(require_permission("quotations:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort: Optional[str] = Query(None, description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_deleted: bool = False,
    search: Optional[str] = None,
):
    query = db.query(Quotation)
    if not include_deleted:
        query = query.filter(Quotation.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'owner_id'):
            query = query.filter(Quotation.owner_id == current_user.id)
        elif hasattr(Quotation, 'assigned_to_id'):
            if hasattr(Quotation, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Quotation.assigned_to_id == current_user.id, Quotation.created_by_id == current_user.id))
            else:
                query = query.filter(Quotation.assigned_to_id == current_user.id)
        elif hasattr(Quotation, 'created_by_id'):
            query = query.filter(Quotation.created_by_id == current_user.id)

    if search:
        search_filters = []
        for field in ['name', 'first_name', 'last_name', 'email', 'phone', 'company', 'subject']:
            if hasattr(Quotation, field):
                search_filters.append(getattr(Quotation, field).ilike(f"%{search}%"))
        if search_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*search_filters))

    # Dynamic Field Filtering
    known_params = {"page", "size", "sort", "order", "include_deleted", "search"}
    for key, value in request.query_params.items():
        if key not in known_params and hasattr(Quotation, key):
            query = query.filter(getattr(Quotation, key) == value)

    # Sorting
    if sort and hasattr(Quotation, sort):
        sort_attr = getattr(Quotation, sort)
        if order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())
    else:
        # Default sort by created_at if it exists
        if hasattr(Quotation, 'created_at'):
            if order == "desc":
                query = query.order_by(Quotation.created_at.desc())
            else:
                query = query.order_by(Quotation.created_at.asc())

    total = query.count()
    offset = (page - 1) * size
    
    items = query.offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }


@router.get("/quotations/{id}", response_model=QuotationRead)
def get_quotation(
    id: UUID,
    current_user: User = Depends(require_permission("quotations:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Quotation).filter(Quotation.id == id, Quotation.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'owner_id'):
            query = query.filter(Quotation.owner_id == current_user.id)
        elif hasattr(Quotation, 'assigned_to_id'):
            if hasattr(Quotation, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Quotation.assigned_to_id == current_user.id, Quotation.created_by_id == current_user.id))
            else:
                query = query.filter(Quotation.assigned_to_id == current_user.id)
        elif hasattr(Quotation, 'created_by_id'):
            query = query.filter(Quotation.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return obj


@router.put("/quotations/{id}", response_model=QuotationRead)
def update_quotation(
    id: UUID,
    payload: QuotationUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("quotations:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Quotation).filter(Quotation.id == id, Quotation.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'owner_id'):
            query = query.filter(Quotation.owner_id == current_user.id)
        elif hasattr(Quotation, 'assigned_to_id'):
            if hasattr(Quotation, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Quotation.assigned_to_id == current_user.id, Quotation.created_by_id == current_user.id))
            else:
                query = query.filter(Quotation.assigned_to_id == current_user.id)
        elif hasattr(Quotation, 'created_by_id'):
            query = query.filter(Quotation.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
        
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    if 'status' in update_data and str(update_data['status']).lower() == 'accepted':
        send_notification(
            db=db,
            user_id=obj.created_by_id or current_user.id,
            title="Quotation Approved",
            message=f"Quotation {getattr(obj, 'quote_number', 'unknown')} has been approved!",
            type=NotificationType.SUCCESS
        )

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/quotations/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quotation(
    id: UUID,
    current_user: User = Depends(require_permission("quotations:delete")),
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    query = db.query(Quotation).filter(Quotation.id == id, Quotation.is_deleted == False)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'owner_id'):
            query = query.filter(Quotation.owner_id == current_user.id)
        elif hasattr(Quotation, 'assigned_to_id'):
            if hasattr(Quotation, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Quotation.assigned_to_id == current_user.id, Quotation.created_by_id == current_user.id))
            else:
                query = query.filter(Quotation.assigned_to_id == current_user.id)
        elif hasattr(Quotation, 'created_by_id'):
            query = query.filter(Quotation.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Quotation not found")
        
    obj.is_deleted = True
    obj.deleted_at = func.now()
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.delete("/quotations/{id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_quotation(
    id: UUID,
    current_user: User = Depends(require_permission("quotations:delete")),
    db: Session = Depends(get_db),
):
    query = db.query(Quotation).filter(Quotation.id == id)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'owner_id'):
            query = query.filter(Quotation.owner_id == current_user.id)
        elif hasattr(Quotation, 'assigned_to_id'):
            if hasattr(Quotation, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Quotation.assigned_to_id == current_user.id, Quotation.created_by_id == current_user.id))
            else:
                query = query.filter(Quotation.assigned_to_id == current_user.id)
        elif hasattr(Quotation, 'created_by_id'):
            query = query.filter(Quotation.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Quotation not found")
        
    db.delete(obj)
    log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)
    db.commit()


@router.post("/quotations/{id}/restore", response_model=QuotationRead)
def restore_quotation(
    id: UUID,
    current_user: User = Depends(require_permission("quotations:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Quotation).filter(Quotation.id == id, Quotation.is_deleted == True)

    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'owner_id'):
            query = query.filter(Quotation.owner_id == current_user.id)
        elif hasattr(Quotation, 'assigned_to_id'):
            if hasattr(Quotation, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Quotation.assigned_to_id == current_user.id, Quotation.created_by_id == current_user.id))
            else:
                query = query.filter(Quotation.assigned_to_id == current_user.id)
        elif hasattr(Quotation, 'created_by_id'):
            query = query.filter(Quotation.created_by_id == current_user.id)

    obj = query.first()
    if not obj:
        raise HTTPException(status_code=404, detail="Quotation not found or not deleted")
        
    obj.is_deleted = False
    obj.deleted_at = None
    log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)
    db.commit()
    db.refresh(obj)
    return obj






# Activity Timeline
@router.get("/leads/{id}/timeline", response_model=List[ActivityRead])
def get_lead_timeline(
    id: UUID,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    activities = db.query(TimelineActivity).filter(
        TimelineActivity.entity_type == "leads",
        TimelineActivity.entity_id == id
    ).order_by(TimelineActivity.created_at.desc()).all()
    
    return activities


@router.post("/leads/{id}/notes", response_model=LeadNoteRead)
def add_lead_note(
    id: UUID,
    payload: LeadNoteCreate,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    note = LeadNote(
        lead_id=id,
        user_id=current_user.id,
        content=payload.content,
        is_pinned=payload.is_pinned
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.get("/leads/{id}/notes", response_model=List[LeadNoteRead])
def get_lead_notes(
    id: UUID,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    notes = db.query(LeadNote).filter(LeadNote.lead_id == id).order_by(LeadNote.created_at.desc()).all()
    return notes


@router.post("/leads/{id}/activities", response_model=LeadActivityRead)
def add_lead_activity(
    id: UUID,
    payload: LeadActivityCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    act_type = payload.type.lower().replace("-", "_").replace(" ", "_")
    if act_type == "phone_call":
        act_type = "call"
        
    activity = LeadActivity(
        lead_id=id,
        user_id=current_user.id,
        type=act_type,
        subject=payload.subject,
        outcome=payload.outcome,
        description=payload.description,
        activity_date=payload.date,
        duration_minutes=payload.duration_minutes
    )
    db.add(activity)
    
    # Add to Timeline
    timeline_activity = TimelineActivity(
        entity_type="leads",
        entity_id=id,
        activity_type=act_type,
        content=f"{payload.type}: {payload.subject}",
        activity_date=payload.date,
        user_id=current_user.id
    )
    db.add(timeline_activity)
    
    db.commit()
    db.refresh(activity)
    if activity.type == 'email' and lead.email:
        background_tasks.add_task(
            send_email,
            lead.email,
            activity.subject or "Follow-up",
            activity.description or f"Hi {lead.first_name},\n\nThis is a follow up regarding our previous conversation.\n\nBest regards,\nSales Team"
        )
    return activity

@router.get("/leads/{id}/activities", response_model=List[LeadActivityRead])
def get_lead_activities(
    id: UUID,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    activities = db.query(LeadActivity).filter(LeadActivity.lead_id == id).order_by(LeadActivity.created_at.desc()).all()
    return activities


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(
    current_user: User = Depends(require_permission("accounts:read")), # Base permission check
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    # 1. Accounts Count
    acc_query = db.query(Account).filter(Account.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            acc_query = acc_query.filter(Account.owner_id == current_user.id)
    accounts_count = acc_query.count()

    # 2. Contacts Count
    cont_query = db.query(Contact).filter(Contact.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            cont_query = cont_query.filter(Contact.owner_id == current_user.id)
    contacts_count = cont_query.count()

    # 3. Leads Count
    lead_query = db.query(Lead).filter(Lead.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            lead_query = lead_query.filter(Lead.owner_id == current_user.id)
    leads_count = lead_query.count()

    # 4. Opportunities Count & Revenue
    opp_query = db.query(Opportunity).filter(Opportunity.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'assigned_to_id'):
            opp_query = opp_query.filter(Opportunity.assigned_to_id == current_user.id)
    
    opportunities_count = opp_query.count()

    # 5. Products Count
    products_count = db.query(Product).filter(Product.is_deleted == False).count()

    # 6. Quotations Count
    quot_query = db.query(Quotation).filter(Quotation.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Quotation, 'created_by_id'):
            quot_query = quot_query.filter(Quotation.created_by_id == current_user.id)
    quotations_count = quot_query.count()

    # 7. Users Count
    users_count = db.query(User).filter(User.is_active == True).count()

    return {
        "accounts": accounts_count,
        "contacts": contacts_count,
        "leads": leads_count,
        "opportunities": opportunities_count,
        "products": products_count,
        "quotations": quotations_count,
        "users": users_count
    }


@router.post("/{module_name}/{id}/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    module_name: str,
    id: UUID,
    payload: ActivityCreate,
    current_user: User = Depends(require_permission("accounts:read")), # Must have basic read access
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    # Validate that module_name is valid
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations"]
    if module_name not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid module name")
        
    activity = TimelineActivity(
        entity_type=module_name,
        entity_id=id,
        activity_type=payload.activity_type,
        content=payload.content,
        activity_date=payload.activity_date or func.now(),
        user_id=current_user.id
    )
    db.add(activity)
    
    # We log this creation to audit logs too
    log_audit(db, current_user, AuditAction.CREATED, "Activity", id)
    
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/{module_name}/{id}/activities", response_model=PaginatedResponse[ActivityRead])
def list_activities(
    module_name: str,
    id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations"]
    if module_name not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid module name")
        
    query = db.query(TimelineActivity).filter(
        TimelineActivity.entity_type == module_name,
        TimelineActivity.entity_id == id
    )
    
    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(TimelineActivity.created_at.desc()).offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }



@router.post("/leads/{id}/convert", response_model=LeadConversionResponse)
def convert_lead(
    id: UUID,
    payload: LeadConvert,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    if lead.is_converted:
        raise HTTPException(status_code=400, detail="Lead is already converted")

    from sqlalchemy.sql import func
    
    try:
        # 1. Handle Account
        account_id = payload.account_id
        if not account_id:
            acc_name = lead.company if lead.company else (lead.first_name + " " + lead.last_name)
            account = Account(
                name=acc_name,
                industry=lead.industry,
                annual_revenue=lead.annual_revenue,
                owner_id=lead.assigned_to_id or current_user.id
            )
            db.add(account)
            db.flush()
            account_id = account.id

        # 2. Handle Contact
        contact_id = payload.contact_id
        if not contact_id:
            contact = Contact(
                first_name=lead.first_name,
                last_name=lead.last_name,
                email=lead.email,
                phone=lead.phone,
                mobile=lead.mobile,
                title=lead.title,
                account_id=account_id,
                owner_id=lead.assigned_to_id or current_user.id
            )
            db.add(contact)
            db.flush()
            contact_id = contact.id

        # 3. Handle Opportunity
        opportunity_id = None
        if payload.create_opportunity:
            opp_name = payload.opportunity_name
            if not opp_name:
                acc_name = lead.company if lead.company else (lead.first_name + " " + lead.last_name)
                opp_name = f"{acc_name} - Deal"
                
            opportunity = Opportunity(
                name=opp_name,
                stage=OpportunityStage.PROSPECTING,
                amount=payload.amount,
                close_date=date.today() + timedelta(days=30),
                account_id=account_id,
                contact_id=contact_id,
                lead_id=lead.id,
                assigned_to_id=lead.assigned_to_id or current_user.id,
                created_by_id=current_user.id
            )
            db.add(opportunity)
            db.flush()
            opportunity_id = opportunity.id

        # 4. Update Lead
        lead.is_converted = True
        lead.status = LeadStatus.CONVERTED
        lead.converted_at = func.now()
        lead.converted_account_id = account_id
        lead.converted_contact_id = contact_id
        lead.converted_opportunity_id = opportunity_id
        
        log_audit(db, current_user, AuditAction.UPDATED, "Lead", lead.id)
        
        db.commit()
        db.refresh(lead)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lead conversion failed: {str(e)}")
    
    return LeadConversionResponse(
        lead_id=lead.id,
        account_id=account_id,
        contact_id=contact_id,
        opportunity_id=opportunity_id,
        status="converted"
    )



@router.get("/dashboard/kpi", response_model=KPIRead)
def get_dashboard_kpi(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
):
    # Base queries with RLS
    lead_query = db.query(Lead).filter(Lead.is_deleted == False)
    opp_query = db.query(Opportunity).filter(Opportunity.is_deleted == False)
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            lead_query = lead_query.filter(Lead.owner_id == current_user.id)
        if hasattr(Opportunity, 'assigned_to_id'):
            opp_query = opp_query.filter(Opportunity.assigned_to_id == current_user.id)
            
    # Lead Conversion Rate
    total_leads = lead_query.count()
    converted_leads = lead_query.filter(Lead.status == LeadStatus.CONVERTED).count()
    conversion_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0.0

    # Win / Loss Rate
    total_opps = opp_query.count()
    won_opps = opp_query.filter(Opportunity.stage == OpportunityStage.CLOSED_WON).count()
    lost_opps = opp_query.filter(Opportunity.stage == OpportunityStage.CLOSED_LOST).count()
    
    win_rate = round((won_opps / total_opps * 100), 2) if total_opps > 0 else 0.0
    lost_rate = round((lost_opps / total_opps * 100), 2) if total_opps > 0 else 0.0

    return {
        "conversion_rate": conversion_rate,
        "win_rate": win_rate,
        "lost_rate": lost_rate
    }



@router.get("/reports/monthly-leads", response_model=List[MonthlyLeadChart])
def get_monthly_leads(
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    query = db.query(Lead).filter(Lead.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
            
    # Group by YYYY-MM
    results = (
        db.query(
            func.to_char(Lead.created_at, 'YYYY-MM').label("month"),
            func.count(Lead.id).label("count")
        )
        .filter(Lead.is_deleted == False)
    )
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            results = results.filter(Lead.owner_id == current_user.id)
            
    results = results.group_by("month").order_by("month").all()
    
    return [{"month": r.month, "count": r.count} for r in results]


@router.get("/reports/revenue", response_model=List[RevenueChart])
def get_revenue_report(
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    # Group by YYYY-MM of close_date
    results = (
        db.query(
            func.to_char(Opportunity.close_date, 'YYYY-MM').label("month"),
            func.sum(Opportunity.amount).label("revenue")
        )
        .filter(Opportunity.is_deleted == False)
    )
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'assigned_to_id'):
            results = results.filter(Opportunity.assigned_to_id == current_user.id)
            
    results = results.group_by("month").order_by("month").all()
    
    return [{"month": r.month, "revenue": float(r.revenue or 0)} for r in results]


@router.get("/reports/funnel", response_model=List[FunnelChart])
def get_funnel_report(
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    results = (
        db.query(
            Opportunity.stage,
            func.count(Opportunity.id).label("count")
        )
        .filter(Opportunity.is_deleted == False)
    )
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'assigned_to_id'):
            results = results.filter(Opportunity.assigned_to_id == current_user.id)
            
    results = results.group_by(Opportunity.stage).all()
    
    return [{"stage": r.stage.value if hasattr(r.stage, 'value') else str(r.stage), "count": r.count} for r in results]



@router.get("/audit-logs", response_model=List[AuditLogRead])
def get_audit_logs(
    current_user: User = Depends(require_permission("accounts:read")), # Must have basic CRM access
    db: Session = Depends(get_db),
):
    # Only show logs related to the user if they are a sales executive, otherwise all
    query = db.query(AuditLog)
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(AuditLog.user_id == current_user.id)
        
    logs = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return logs

# Users
@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_permission("users:create")),
    db: Session = Depends(get_db),
):
    user = User(**payload.model_dump(exclude_none=True, exclude={"password"}))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=List[UserRead])
def list_users(
    current_user: User = Depends(require_permission("users:read")),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    return db.query(User).offset(skip).limit(limit).all()
