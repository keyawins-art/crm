from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.models.sales_order import SalesOrderStatus


class SalesOrderBase(BaseModel):
    order_number: str
    status: SalesOrderStatus = SalesOrderStatus.DRAFT
    total_amount: float = Field(ge=0)
    quotation_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None


class SalesOrderCreate(SalesOrderBase):
    pass


class SalesOrderRead(SalesOrderBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
