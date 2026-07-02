

from sqlalchemy import Column, String, Text, Numeric, Boolean, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class ProductCategory(str, enum.Enum):
    SOFTWARE = "software"
    HARDWARE = "hardware"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"
    CONSULTING = "consulting"
    SUPPORT = "support"
    OTHER = "other"


class Product(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    name = Column(String(255), nullable=False, index=True)
    code = Column(String(100), unique=True, nullable=True)          
    description = Column(Text, nullable=True)
    category = Column(SAEnum(ProductCategory), nullable=True)
    status = Column(SAEnum(ProductStatus), default=ProductStatus.ACTIVE, nullable=False, index=True)
    image_url = Column(String(255), nullable=True)
    specifications = Column(JSONB, nullable=True)

    # Pricing
    list_price = Column(Numeric(15, 2), nullable=False, default=0)  
    cost_price = Column(Numeric(15, 2), nullable=True)                
    currency = Column(String(3), default="INR", nullable=False)

    # Inventory
    has_inventory = Column(Boolean, default=False, nullable=False)
    quantity_in_stock = Column(Integer, default=0, nullable=False)
    units_sold = Column(Integer, default=0, nullable=False)

    # Tax
    tax_rate = Column(Numeric(5, 2), nullable=True)              
    hsn_code = Column(String(20), nullable=True)                      

    # Relationships
    price_book_entries = relationship("PriceBookEntry", back_populates="product", lazy="dynamic")
    opportunity_products = relationship("OpportunityProduct", back_populates="product", lazy="dynamic")
    quotation_items = relationship("QuotationItem", back_populates="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product {self.name} [{self.code}]>"


class PriceBook(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "price_books"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_standard = Column(Boolean, default=False, nullable=False)      
    is_active = Column(Boolean, default=True, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    # Relationships
    entries = relationship("PriceBookEntry", back_populates="price_book", lazy="dynamic")
    opportunities = relationship("Opportunity", back_populates="price_book", lazy="dynamic")
    quotations = relationship("Quotation", back_populates="price_book", lazy="dynamic")

    def __repr__(self):
        return f"<PriceBook {self.name}>"


class PriceBookEntry(Base, UUIDMixin, TimestampMixin):
    """Product ka price in a specific PriceBook."""
    __tablename__ = "price_book_entries"

    price_book_id = Column(UUID(as_uuid=True), ForeignKey("price_books.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    unit_price = Column(Numeric(15, 2), nullable=False)              
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    price_book = relationship("PriceBook", back_populates="entries", lazy="joined")
    product = relationship("Product", back_populates="price_book_entries", lazy="joined")

    def __repr__(self):
        return f"<PriceBookEntry {self.product_id} in {self.price_book_id}>"