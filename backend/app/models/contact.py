
from sqlalchemy import Column, String, Text, ForeignKey, Enum as SAEnum, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class ContactSalutation(str, enum.Enum):
    MR = "Mr"
    MRS = "Mrs"
    MS = "Ms"
    DR = "Dr"
    PROF = "Prof"


class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Contact(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contacts"

    # Name
    salutation = Column(SAEnum(ContactSalutation), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Professional
    title = Column(String(100), nullable=True)          # Job title
    department = Column(String(100), nullable=True)

    # Contact Info
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    linkedin_url = Column(String(255), nullable=True)

    # Personal
    date_of_birth = Column(Date, nullable=True)

    # Address
    mailing_street = Column(String(255), nullable=True)
    mailing_city = Column(String(100), nullable=True)
    mailing_state = Column(String(100), nullable=True)
    mailing_country = Column(String(100), nullable=True)
    mailing_pincode = Column(String(20), nullable=True)

    # Meta
    status = Column(SAEnum(ContactStatus), default=ContactStatus.ACTIVE, nullable=False)
    description = Column(Text, nullable=True)
    do_not_email = Column(Boolean, default=False, nullable=False)
    do_not_call = Column(Boolean, default=False, nullable=False)

    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    reported_to_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True
    )  # Manager / Reports To (self-referential)

    
    account = relationship("Account", back_populates="contacts", lazy="joined")
    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    reported_to = relationship("Contact", remote_side="Contact.id", lazy="joined")
    leads = relationship("Lead", back_populates="contact", lazy="dynamic")

    @property
    def full_name(self):
        parts = [self.salutation, self.first_name, self.last_name]
        return " ".join(p for p in parts if p)

    def __repr__(self):
        return f"<Contact {self.full_name}>"