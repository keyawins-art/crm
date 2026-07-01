from sqlalchemy import Column, String, Text
from app.models.base import Base, UUIDMixin, TimestampMixin

class CompanySettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "company_settings"

    company_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    gst_number = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    bank_name = Column(String(255), nullable=True)
    bank_branch = Column(String(255), nullable=True)
    bank_account_no = Column(String(100), nullable=True)
    bank_ifsc = Column(String(50), nullable=True)
    logo_url = Column(Text, nullable=True)
