import enum
from sqlalchemy import Column, String, Numeric, Enum as SAEnum, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "invoices"

    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SAEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    amount_paid = Column(Numeric(15, 2), nullable=False, default=0.00)
    due_date = Column(Date, nullable=True)

    # Foreign Keys
    sales_order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id", ondelete="SET NULL"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    sales_order = relationship("SalesOrder", back_populates="invoices", lazy="joined")
    account = relationship("Account", lazy="joined")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} [{self.status}]>"
