import enum
from sqlalchemy import Column, String, Numeric, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class SalesOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class SalesOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sales_orders"

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SAEnum(SalesOrderStatus), default=SalesOrderStatus.DRAFT, nullable=False, index=True)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)

    # Foreign Keys
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    quotation = relationship("Quotation", lazy="joined")
    account = relationship("Account", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    invoices = relationship("Invoice", back_populates="sales_order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SalesOrder {self.order_number} [{self.status}]>"
