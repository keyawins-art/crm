from typing import Optional
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.invoice import InvoiceStatus


class InvoiceBase(BaseModel):
    invoice_number: str
    status: InvoiceStatus = InvoiceStatus.DRAFT
    total_amount: float = Field(..., ge=0.0)
    amount_paid: float = Field(0.0, ge=0.0)
    due_date: Optional[date] = None
    sales_order_id: Optional[UUID] = None
    account_id: Optional[UUID] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceRead(InvoiceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
