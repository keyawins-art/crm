import enum
from sqlalchemy import Column, String, Numeric, Enum as SAEnum, ForeignKey, Date, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class SalesOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class SalesOrderPriority(str, enum.Enum):
    STANDARD = "Standard"
    EXPRESS = "Express"
    URGENT = "Urgent"

class SalesOrderPaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"


class SalesOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sales_orders"

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SAEnum(SalesOrderStatus), default=SalesOrderStatus.DRAFT, nullable=False, index=True)
    priority = Column(SAEnum(SalesOrderPriority), default=SalesOrderPriority.STANDARD, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    
    order_date = Column(Date, nullable=True)
    ship_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    
    ship_to = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    
    payment_status = Column(SAEnum(SalesOrderPaymentStatus), default=SalesOrderPaymentStatus.PENDING, nullable=False)
    payment_method = Column(String(100), nullable=True)

    # Foreign Keys
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    quotation = relationship("Quotation", lazy="joined")
    account = relationship("Account", lazy="joined")
    opportunity = relationship("Opportunity", lazy="joined")
    assignee = relationship("User", lazy="joined")
    invoices = relationship("Invoice", back_populates="sales_order", cascade="all, delete-orphan")
    items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<SalesOrder {self.order_number} [{self.status}]>"

class SalesOrderItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sales_order_items"

    sales_order_id = Column(UUID(as_uuid=True), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=True)
    
    sku = Column(String(100), nullable=True)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    
    quantity = Column(Numeric(10, 2), nullable=False, default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=True)

    sales_order = relationship("SalesOrder", back_populates="items")
    product = relationship("Product", lazy="joined")
