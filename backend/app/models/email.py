import enum
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin


class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class EmailLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_logs"

    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    
    status = Column(SAEnum(EmailStatus), default=EmailStatus.PENDING, nullable=False)
    sent_time = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # CRM Entities (Optional, for linking the log to a specific record)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, index=True)

    sender = relationship("User", lazy="joined")
    lead = relationship("Lead", lazy="selectin")
    contact = relationship("Contact", lazy="selectin")
    opportunity = relationship("Opportunity", lazy="selectin")

    def __repr__(self):
        return f"<EmailLog {self.recipient} [{self.status}]>"
