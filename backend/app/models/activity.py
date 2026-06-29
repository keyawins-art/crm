from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin
from .lead import ActivityType

class TimelineActivity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "timeline_activities"

    entity_type = Column(String(50), nullable=False, index=True) # e.g. "accounts", "leads"
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    activity_type = Column(SAEnum(ActivityType), nullable=False)
    content = Column(Text, nullable=False)
    activity_date = Column(DateTime(timezone=True), nullable=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    user = relationship("User", lazy="joined")

    def __repr__(self):
        return f"<TimelineActivity {self.activity_type} on {self.entity_type}/{self.entity_id}>"
