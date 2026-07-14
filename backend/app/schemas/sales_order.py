from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.sales_order import SalesOrderStatus, SalesOrderPriority, SalesOrderPaymentStatus


class SalesOrderBase(BaseModel):
    order_number: str
    status: SalesOrderStatus = SalesOrderStatus.DRAFT
    priority: SalesOrderPriority = SalesOrderPriority.STANDARD
    total_amount: float = Field(ge=0)
    
    order_date: Optional[date] = None
    ship_date: Optional[date] = None
    delivery_date: Optional[date] = None
    
    ship_to: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    
    payment_status: SalesOrderPaymentStatus = SalesOrderPaymentStatus.PENDING
    payment_method: Optional[str] = None

    quotation_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None

class SalesOrderItemRead(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    sku: Optional[str] = None
    product_name: str
    category: Optional[str] = None
    quantity: float
    unit_price: float
    discount_percent: float
    total_price: float
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AccountMinimal(BaseModel):
    id: UUID
    name: str
    industry: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_city: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class OpportunityMinimal(BaseModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)

class UserMinimal(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    model_config = ConfigDict(from_attributes=True)


class SalesOrderCreate(SalesOrderBase):
    pass


class SalesOrderRead(SalesOrderBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    # We can include nested relationships if needed, e.g. for the frontend
    items: List[SalesOrderItemRead] = []
    
    account: Optional[AccountMinimal] = None
    opportunity: Optional[OpportunityMinimal] = None
    assignee: Optional[UserMinimal] = None

    model_config = ConfigDict(from_attributes=True)
