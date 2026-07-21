from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class DocumentRead(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    filename: str
    content_type: str
    file_size: int
    category: str | None = None
    uploaded_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    download_url: str

    model_config = ConfigDict(from_attributes=True)