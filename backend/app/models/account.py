
from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class AccountType(str, enum.Enum):
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    PARTNER = "partner"
    VENDOR = "vendor"
    COMPETITOR = "competitor"
    OTHER = "other"


class AccountIndustry(str, enum.Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    REAL_ESTATE = "real_estate"
    HOSPITALITY = "hospitality"
    LOGISTICS = "logistics"
    OTHER = "other"


class Account(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "accounts"

    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    type = Column(SAEnum(AccountType), default=AccountType.PROSPECT, nullable=False, index=True)
    industry = Column(SAEnum(AccountIndustry), nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    # Address
    billing_street = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_country = Column(String(100), nullable=True)
    billing_pincode = Column(String(20), nullable=True)

    shipping_street = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    shipping_pincode = Column(String(20), nullable=True)

    # Business Details
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    employee_count = Column(Integer, nullable=True)
    gst_number = Column(String(20), nullable=True)
    pan_number = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)

    # Ownership
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    contacts = relationship("Contact", back_populates="account", lazy="dynamic")
    leads = relationship("Lead", back_populates="account", lazy="dynamic")
    opportunities = relationship("Opportunity", back_populates="account", lazy="dynamic")

    def __repr__(self):
        return f"<Account {self.name} [{self.type}]>"