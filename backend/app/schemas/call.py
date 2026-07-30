from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.call import CallType


class CallBase(BaseModel):
    phone_number: str = Field(..., max_length=50)
    call_type: CallType = CallType.OUTBOUND
    duration: Optional[int] = None
    outcome: Optional[str] = Field(None, max_length=100)
    recording_url: Optional[str] = Field(None, max_length=500)
    transcript: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    
    lead_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None


class CallCreate(CallBase):
    pass


class CallRead(CallBase):
    id: UUID
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
