from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.integration import IntegrationProvider, IntegrationStatus


class IntegrationConfigBase(BaseModel):
    provider_name: IntegrationProvider
    is_enabled: bool = False
    # NOTE: credentials are NEVER returned in API responses


class IntegrationConnect(BaseModel):
    credentials: Dict[str, Any] = {}


class IntegrationConfigRead(IntegrationConfigBase):
    """Response schema — deliberately omits credentials."""
    id: UUID
    status: IntegrationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
