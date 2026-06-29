import math
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.core.rbac import require_permission
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
    LeadCreate, LeadRead, LeadUpdate,
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


@router.get("/health", include_in_schema=False)
def health_check():
    return {"status": "ok"}






# Accounts
@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
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
    db.commit()
    db.refresh(obj)
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
        
    db.commit()
    db.refresh(obj)
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
    obj = Contact(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.commit()
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
    db.commit()
    db.refresh(obj)
    return obj


# Leads
@router.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    current_user: User = Depends(require_permission("leads:create")),
    db: Session = Depends(get_db),
):
    obj = Lead(**payload.model_dump(exclude_none=True))
    
    # Auto-assign ownership if applicable
    if hasattr(obj, 'owner_id') and not getattr(obj, 'owner_id', None):
        obj.owner_id = current_user.id
    elif hasattr(obj, 'assigned_to_id') and not getattr(obj, 'assigned_to_id', None):
        obj.assigned_to_id = current_user.id
        
    if hasattr(obj, 'created_by_id') and not getattr(obj, 'created_by_id', None):
        obj.created_by_id = current_user.id

    db.add(obj)
    db.commit()
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
    db.commit()
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
    db.commit()
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
    db.commit()
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
    db.commit()
    db.refresh(obj)
    return obj


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
