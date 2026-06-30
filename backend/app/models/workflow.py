import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Enum as SAEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin


class WorkflowActionType(str, enum.Enum):
    ASSIGN_USER = "assign_user"
    CREATE_TASK = "create_task"
    SEND_EMAIL = "send_email"
    NOTIFY_USER = "notify_user"


class WorkflowRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_rules"

    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    trigger_entity = Column(String(50), nullable=False, index=True) # e.g. "Lead", "Opportunity"
    trigger_event = Column(String(50), nullable=False, index=True)  # e.g. "created", "updated"
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    actions = relationship("WorkflowAction", back_populates="rule", order_by="WorkflowAction.execution_order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WorkflowRule {self.name} on {self.trigger_entity}_{self.trigger_event}>"


class WorkflowAction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "workflow_actions"

    rule_id = Column(UUID(as_uuid=True), ForeignKey("workflow_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type = Column(SAEnum(WorkflowActionType), nullable=False)
    action_params = Column(JSON, nullable=False, default=dict) # E.g., {"user_id": "...", "subject": "Welcome"}
    execution_order = Column(Integer, default=0, nullable=False)

    # Relationships
    rule = relationship("WorkflowRule", back_populates="actions")

    def __repr__(self):
        return f"<WorkflowAction {self.action_type} for Rule {self.rule_id}>"
