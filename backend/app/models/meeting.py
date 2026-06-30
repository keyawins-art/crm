import enum
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class MeetingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Meeting(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "meetings"

    subject = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    meeting_link = Column(String(500), nullable=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    # Store attendees as a JSON list of emails or names
    attendees = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(SAEnum(MeetingStatus), default=MeetingStatus.SCHEDULED, nullable=False)
    
    # Relationships
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # CRM Entities
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, index=True)

    created_by = relationship("User", lazy="joined")
    lead = relationship("Lead", lazy="selectin")
    contact = relationship("Contact", lazy="selectin")
    opportunity = relationship("Opportunity", lazy="selectin")

    def __repr__(self):
        return f"<Meeting {self.subject} [{self.status}]>"
