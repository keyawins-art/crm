from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PaymentBase(BaseModel):
    payment_number: str
    amount: float = Field(ge=0)
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    transaction_reference: Optional[str] = None
    invoice_id: UUID


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
