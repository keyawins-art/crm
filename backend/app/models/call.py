import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class CallType(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Call(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "calls"

    phone_number = Column(String(50), nullable=False)
    call_type = Column(SAEnum(CallType), nullable=False, default=CallType.OUTBOUND)
    duration = Column(Integer, nullable=True) # Duration in seconds
    outcome = Column(String(100), nullable=True) # e.g. "Left Voicemail", "Connected", "No Answer"
    recording_url = Column(String(500), nullable=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    
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
        return f"<Call {self.phone_number} [{self.call_type}]>"
