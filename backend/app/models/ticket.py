import enum
from sqlalchemy import Column, String, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tickets"

    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)
    priority = Column(SAEnum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)

    # Foreign Keys
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")

    def __repr__(self):
        return f"<Ticket {self.ticket_number} [{self.status}]>"
