
from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class AccountType(str, enum.Enum):
    PROSPECT = "PROSPECT"
    CUSTOMER = "CUSTOMER"
    PARTNER = "PARTNER"
    VENDOR = "VENDOR"
    COMPETITOR = "COMPETITOR"
    OTHER = "OTHER"


class AccountIndustry(str, enum.Enum):
    TECHNOLOGY = "TECHNOLOGY"
    FINANCE = "FINANCE"
    HEALTHCARE = "HEALTHCARE"
    EDUCATION = "EDUCATION"
    MANUFACTURING = "MANUFACTURING"
    RETAIL = "RETAIL"
    REAL_ESTATE = "REAL_ESTATE"
    HOSPITALITY = "HOSPITALITY"
    LOGISTICS = "LOGISTICS"
    OTHER = "OTHER"


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

    # Added custom customer fields
    contact_name = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    product_of_interest = Column(String(255), nullable=True)

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
    leads = relationship(
    "Lead",
        back_populates="account",
        foreign_keys="Lead.account_id",
        lazy="dynamic")

    converted_leads = relationship(
        "Lead",
        foreign_keys="Lead.converted_account_id",
        lazy="dynamic"
    )
    opportunities = relationship("Opportunity", back_populates="account", lazy="dynamic")

    def __repr__(self):
        return f"<Account {self.name} [{self.type}]>"