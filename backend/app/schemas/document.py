from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class DocumentRead(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    filename: str
    file_path: str
    content_type: str
    file_size: int
    category: Optional[str] = None
    
    uploaded_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
