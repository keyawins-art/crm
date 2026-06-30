from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.workflow import WorkflowActionType


class WorkflowActionBase(BaseModel):
    action_type: WorkflowActionType
    action_params: Dict[str, Any] = Field(default_factory=dict)
    execution_order: int = 0


class WorkflowActionCreate(WorkflowActionBase):
    pass


class WorkflowActionRead(WorkflowActionBase):
    id: UUID
    rule_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowRuleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    trigger_entity: str = Field(..., max_length=50)
    trigger_event: str = Field(..., max_length=50)
    is_active: bool = True


class WorkflowRuleCreate(WorkflowRuleBase):
    actions: List[WorkflowActionCreate] = Field(default_factory=list)


class WorkflowRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class WorkflowRuleRead(WorkflowRuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    actions: List[WorkflowActionRead] = []

    model_config = ConfigDict(from_attributes=True)
