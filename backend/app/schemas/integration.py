from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.integration import IntegrationProvider, IntegrationStatus


class IntegrationConfigBase(BaseModel):
    provider_name: IntegrationProvider
    is_enabled: bool = False
    credentials: Dict[str, Any] = {}


class IntegrationConnect(BaseModel):
    credentials: Dict[str, Any] = {}


class IntegrationConfigRead(IntegrationConfigBase):
    id: UUID
    status: IntegrationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
