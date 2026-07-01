from sqlalchemy import Column, String, Text, Numeric, Boolean, ForeignKey, Enum as SAEnum, Integer, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin




class OpportunityStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_PROPOSITION = "value_proposition"
    ID_DECISION_MAKERS = "id_decision_makers"
    PERCEPTION_ANALYSIS = "perception_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class OpportunityType(str, enum.Enum):
    NEW_BUSINESS = "new_business"
    EXISTING_BUSINESS = "existing_business"
    RENEWAL = "renewal"
    UPSELL = "upsell"
    CROSS_SELL = "cross_sell"


class QuotationStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Opportunity(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "opportunities"

    name = Column(String(255), nullable=False, index=True)
    type = Column(SAEnum(OpportunityType), nullable=True)
    stage = Column(SAEnum(OpportunityStage), default=OpportunityStage.PROSPECTING, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Financials
    amount = Column(Numeric(15, 2), nullable=True)
    expected_revenue = Column(Numeric(15, 2), nullable=True)
    probability = Column(Numeric(5, 2), nullable=True)                # 0-100 %
    currency = Column(String(3), default="INR", nullable=False)

    # Dates
    close_date = Column(Date, nullable=False)
    actual_close_date = Column(Date, nullable=True)

    # Outcome
    is_won = Column(Boolean, nullable=True)                            # True=Won, False=Lost, None=Open
    loss_reason = Column(Text, nullable=True)
    competitor = Column(String(255), nullable=True)

    # Foreign Keys
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    price_book_id = Column(UUID(as_uuid=True), ForeignKey("price_books.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    account = relationship("Account", back_populates="opportunities", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    lead = relationship("Lead", lazy="joined")
    price_book = relationship("PriceBook", back_populates="opportunities", lazy="joined")
    assigned_to = relationship("User", back_populates="assigned_opportunities", foreign_keys=[assigned_to_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")
    products = relationship("OpportunityProduct", back_populates="opportunity", lazy="selectin", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="opportunity", lazy="dynamic")

    def __repr__(self):
        return f"<Opportunity {self.name} [{self.stage}]>"


class OpportunityProduct(Base, UUIDMixin, TimestampMixin):
    """Line items attached to an Opportunity."""
    __tablename__ = "opportunity_products"

    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    price_book_entry_id = Column(UUID(as_uuid=True), ForeignKey("price_book_entries.id", ondelete="SET NULL"), nullable=True)

    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)
    tax_percent = Column(Numeric(5, 2), default=0, nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)              # Computed: qty * price * (1 - discount) * (1 + tax)

    description = Column(Text, nullable=True)                         # Line item description

    # Relationships
    opportunity = relationship("Opportunity", back_populates="products")
    product = relationship("Product", back_populates="opportunity_products", lazy="joined")

    def __repr__(self):
        return f"<OpportunityProduct {self.product_id} x{self.quantity}>"




class Quotation(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "quotations"

    quote_number = Column(String(50), unique=True, nullable=False, index=True)  # e.g. QT-2024-0001
    subject = Column(String(255), nullable=False)
    status = Column(SAEnum(QuotationStatus), default=QuotationStatus.DRAFT, nullable=False, index=True)

    # Dates
    valid_until = Column(Date, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    # Financials
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    shipping_amount = Column(Numeric(15, 2), default=0, nullable=False)
    grand_total = Column(Numeric(15, 2), default=0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    # Terms
    terms_and_conditions = Column(Text, nullable=True)
    payment_terms = Column(String(255), nullable=True)
    delivery_terms = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Address Overrides
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)

    # Foreign Keys
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    price_book_id = Column(UUID(as_uuid=True), ForeignKey("price_books.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    opportunity = relationship("Opportunity", back_populates="quotations", lazy="joined")
    account = relationship("Account", lazy="joined")
    contact = relationship("Contact", lazy="joined")
    price_book = relationship("PriceBook", back_populates="quotations", lazy="joined")
    created_by = relationship("User", lazy="joined")
    items = relationship("QuotationItem", back_populates="quotation", lazy="selectin", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quotation {self.quote_number} [{self.status}]>"


class QuotationItem(Base, UUIDMixin, TimestampMixin):
    """Line items in a Quotation."""
    __tablename__ = "quotation_items"

    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)

    sort_order = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)
    tax_percent = Column(Numeric(5, 2), default=0, nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)

    # Relationships
    quotation = relationship("Quotation", back_populates="items")
    product = relationship("Product", back_populates="quotation_items", lazy="joined")

    def __repr__(self):
        return f"<QuotationItem {self.product_id} x{self.quantity}>"