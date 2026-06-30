from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.ticket import TicketStatus, TicketPriority


class TicketBase(BaseModel):
    subject: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    subject: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    account_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None


class TicketCommentCreate(BaseModel):
    content: str
    is_internal: bool = False


class TicketCommentRead(BaseModel):
    id: UUID
    content: str
    is_internal: bool
    ticket_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketRead(TicketBase):
    id: UUID
    ticket_number: str
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    comments: List[TicketCommentRead] = []

    model_config = ConfigDict(from_attributes=True)
