from datetime import date, datetime
from typing import Optional, Generic, TypeVar, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    size: int
    total: int
    pages: int


class CRMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AccountCreate(CRMBase):
    name: str
    type: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None


class AccountRead(AccountCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AccountUpdate(CRMBase):
    name: Optional[str] = None
    type: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None


class ContactCreate(CRMBase):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    account_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    status: Optional[str] = None


class ContactRead(ContactCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContactUpdate(CRMBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    account_id: Optional[UUID] = None
    owner_id: Optional[UUID] = None
    status: Optional[str] = None


class LeadCreate(CRMBase):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[str] = None
    source_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class LeadRead(LeadCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LeadUpdate(CRMBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[str] = None
    source_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class ProductCreate(CRMBase):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    list_price: Optional[float] = None
    cost_price: Optional[float] = None
    currency: Optional[str] = None


class ProductRead(ProductCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductUpdate(CRMBase):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    list_price: Optional[float] = None
    cost_price: Optional[float] = None
    currency: Optional[str] = None


class OpportunityCreate(CRMBase):
    name: str
    type: Optional[str] = None
    stage: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    close_date: Optional[date] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class OpportunityRead(OpportunityCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OpportunityUpdate(CRMBase):
    name: Optional[str] = None
    type: Optional[str] = None
    stage: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    close_date: Optional[date] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class QuotationCreate(CRMBase):
    quote_number: str
    subject: str
    status: Optional[str] = None
    opportunity_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    grand_total: Optional[float] = None


class QuotationRead(QuotationCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuotationUpdate(CRMBase):
    quote_number: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    opportunity_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    grand_total: Optional[float] = None


class UserCreate(CRMBase):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    password: str
    role_id: Optional[UUID] = None
    status: Optional[str] = None


class UserRead(CRMBase):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
