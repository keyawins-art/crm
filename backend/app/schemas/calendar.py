from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CalendarEvent(BaseModel):
    id: UUID
    type: str  # "task", "meeting", "call"
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    
    # Metadata for linking
    lead_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)
