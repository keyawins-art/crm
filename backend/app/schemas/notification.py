from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.audit import NotificationType

class NotificationCreate(BaseModel):
    user_id: UUID
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO

class NotificationRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
