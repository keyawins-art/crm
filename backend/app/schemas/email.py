from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.email import EmailStatus


class EmailBase(BaseModel):
    recipient: str = Field(..., max_length=255)
    subject: str = Field(..., max_length=500)
    body: str
    
    lead_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None


class EmailSendRequest(EmailBase):
    pass


class EmailLogRead(EmailBase):
    id: UUID
    status: EmailStatus
    sent_time: Optional[datetime] = None
    sender_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
