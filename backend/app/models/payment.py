import enum
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .base import Base, UUIDMixin, TimestampMixin


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    payment_method = Column(String(50), nullable=True) # e.g., Credit Card, Razorpay, Stripe
    transaction_reference = Column(String(100), nullable=True)

    # Foreign Keys
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments", lazy="joined")

    def __repr__(self):
        return f"<Payment {self.payment_number} for Invoice {self.invoice_id}>"
