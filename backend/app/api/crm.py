from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
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
    AccountCreate,
    AccountRead,
    ContactCreate,
    ContactRead,
    LeadCreate,
    LeadRead,
    OpportunityCreate,
    OpportunityRead,
    ProductCreate,
    ProductRead,
    QuotationCreate,
    QuotationRead,
    UserCreate,
    UserRead,
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
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    account = Account(**payload.model_dump(exclude_none=True))
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts", response_model=List[AccountRead])
def list_accounts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Account).offset(skip).limit(limit).all()


@router.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(account_id: UUID, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


# Contacts
@router.post("/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(**payload.model_dump(exclude_none=True))
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/contacts", response_model=List[ContactRead])
def list_contacts(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Contact).offset(skip).limit(limit).all()


# Leads
@router.post("/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(**payload.model_dump(exclude_none=True))
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads", response_model=List[LeadRead])
def list_leads(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Lead).offset(skip).limit(limit).all()


# Products
@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump(exclude_none=True))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products", response_model=List[ProductRead])
def list_products(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Product).offset(skip).limit(limit).all()


# Opportunities
@router.post("/opportunities", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db)):
    opportunity = Opportunity(**payload.model_dump(exclude_none=True))
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


@router.get("/opportunities", response_model=List[OpportunityRead])
def list_opportunities(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Opportunity).offset(skip).limit(limit).all()


# Quotations
@router.post("/quotations", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
def create_quotation(payload: QuotationCreate, db: Session = Depends(get_db)):
    quotation = Quotation(**payload.model_dump(exclude_none=True))
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.get("/quotations", response_model=List[QuotationRead])
def list_quotations(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(Quotation).offset(skip).limit(limit).all()


# Users
@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(**payload.model_dump(exclude_none=True, exclude={"password"}))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()
