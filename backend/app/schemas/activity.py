from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.lead import ActivityType

class ActivityCreate(BaseModel):
    activity_type: ActivityType
    content: str
    activity_date: Optional[datetime] = None

class ActivityRead(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    activity_type: ActivityType
    content: str
    activity_date: Optional[datetime] = None
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
