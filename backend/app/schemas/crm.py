from datetime import date, datetime
from typing import Optional, Generic, TypeVar, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    contact_name: Optional[str] = None
    source: Optional[str] = None
    product_of_interest: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    owner_id: Optional[UUID] = None


class AccountRead(AccountCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    owner: Optional["UserRead"] = None


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
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    contact_name: Optional[str] = None
    source: Optional[str] = None
    product_of_interest: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    owner_id: Optional[UUID] = None


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
    address: Optional[str] = None
    next_followup_date: Optional[datetime] = None
    requirements: Optional[str] = None
    remarks: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    ai_score: Optional[float] = None
    ai_priority_explanation: Optional[str] = None


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
    address: Optional[str] = None
    next_followup_date: Optional[datetime] = None
    requirements: Optional[str] = None
    remarks: Optional[str] = None
    source: Optional[str] = None
    source_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    ai_score: Optional[float] = None
    ai_priority_explanation: Optional[str] = None


class LeadConvert(CRMBase):
    create_opportunity: bool = True
    opportunity_name: Optional[str] = None
    amount: Optional[float] = Field(None, ge=0.0)
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None

class LeadConversionResponse(BaseModel):
    lead_id: UUID
    account_id: UUID
    contact_id: UUID
    opportunity_id: Optional[UUID] = None
    status: str


class ProductCreate(CRMBase):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    list_price: Optional[float] = None
    cost_price: Optional[float] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    specifications: Optional[dict] = None


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
    image_url: Optional[str] = None
    specifications: Optional[dict] = None


class OpportunityCreate(CRMBase):
    name: str
    type: Optional[str] = None
    stage: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = Field(None, ge=0.0)
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
    amount: Optional[float] = Field(None, ge=0.0)
    close_date: Optional[date] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class QuotationItemCreate(CRMBase):
    product_id: UUID
    description: Optional[str] = None
    quantity: float = 1
    unit_price: float = 0.0
    discount_percent: float = 0.0
    tax_percent: float = 0.0

class QuotationItemRead(QuotationItemCreate):
    id: UUID
    total_price: float

class QuotationCreate(CRMBase):
    quote_number: str
    subject: str
    status: Optional[str] = None
    opportunity_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    
    # Financials (calculated dynamically on backend if items provided)
    subtotal: Optional[float] = 0
    tax_amount: Optional[float] = 0
    grand_total: Optional[float] = 0
    
    # Terms
    terms_and_conditions: Optional[str] = None
    payment_terms: Optional[str] = None
    
    # Address Overrides
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    
    # Line items
    items: Optional[List[QuotationItemCreate]] = []

class QuotationRead(QuotationCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: Optional[List[QuotationItemRead]] = []
    account: Optional[AccountRead] = None


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
    role_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserUpdate(CRMBase):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[UUID] = None
    status: Optional[str] = None


class RoleRead(CRMBase):
    id: UUID
    name: str
    description: Optional[str] = None


class LeadNoteCreate(BaseModel):
    content: str
    is_pinned: Optional[bool] = False

class LeadNoteRead(LeadNoteCreate):
    id: UUID
    lead_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class LeadActivityCreate(BaseModel):
    type: str
    subject: str
    outcome: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    duration_minutes: Optional[str] = None

class LeadActivityRead(BaseModel):
    id: UUID
    lead_id: UUID
    user_id: Optional[UUID] = None
    type: str
    subject: str
    outcome: Optional[str] = None
    description: Optional[str] = None
    activity_date: Optional[datetime] = None
    duration_minutes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class DashboardRead(BaseModel):
    accounts: int
    contacts: int
    leads: int
    opportunities: int
    products: int
    quotations: int
    users: int


class KPIRead(BaseModel):
    conversion_rate: float
    win_rate: float
    lost_rate: float


class MonthlyLeadChart(BaseModel):
    month: str
    count: int

class RevenueChart(BaseModel):
    month: str
    revenue: float

class FunnelChart(BaseModel):
    stage: str
    count: int


class AuditLogRead(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    entity_type: str
    entity_id: Optional[UUID] = None
    action: str
    details: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
