from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.meeting import MeetingStatus


class MeetingBase(BaseModel):
    subject: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    meeting_link: Optional[str] = Field(None, max_length=500)
    
    start_time: datetime
    end_time: datetime
    
    attendees: Optional[List[Any]] = None
    notes: Optional[str] = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    
    lead_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingRead(MeetingBase):
    id: UUID
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
