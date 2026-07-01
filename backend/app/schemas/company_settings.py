from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class CRMBase(BaseModel):
    class Config:
        from_attributes = True

class CompanySettingsCreate(CRMBase):
    company_name: str
    address: Optional[str] = None
    gst_number: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    logo_url: Optional[str] = None

class CompanySettingsRead(CompanySettingsCreate):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CompanySettingsUpdate(CRMBase):
    company_name: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    logo_url: Optional[str] = None
