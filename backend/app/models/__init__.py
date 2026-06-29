from .base import Base, TimestampMixin, SoftDeleteMixin, UUIDMixin 
# Module 1 — Auth & RBAC
from .role import Role, Permission, RolePermission
from .user import User, UserStatus
 
# Module 2 — CRM Core
from .account import Account, AccountType, AccountIndustry
from .contact import Contact, ContactSalutation, ContactStatus
 
# Module 3 — Leads
from .lead import LeadSource, LeadSourceType, Lead, LeadStatus, LeadRating
from .lead import LeadActivity, ActivityType, ActivityOutcome
from .lead import LeadNote
 
# Module 4 — Products & Pricing
from .product import Product, ProductStatus, ProductCategory
from .product import PriceBook, PriceBookEntry
 
# Module 5 — Opportunities & Quotations
from .opportunity import Opportunity, OpportunityStage, OpportunityType
from .opportunity import OpportunityProduct
from .opportunity import Quotation, QuotationStatus, QuotationItem
 
# Module 6 — Activity & Documents
from .activity import TimelineActivity
from .document import Document

# Module 7 — System
from .audit import AuditLog, AuditAction
from .audit import Notification, NotificationType

__all__ = [
    # Base
    "Base",
 
    # Auth
    "Role", "Permission", "RolePermission",
    "User", "UserStatus",
 
    # CRM Core
    "Account", "AccountType", "AccountIndustry",
    "Contact", "ContactSalutation", "ContactStatus",
 
    # Leads
    "LeadSource", "LeadSourceType",
    "Lead", "LeadStatus", "LeadRating",
    "LeadActivity", "ActivityType", "ActivityOutcome",
    "LeadNote",
 
    # Products
    "Product", "ProductStatus", "ProductCategory",
    "PriceBook", "PriceBookEntry",
 
    # Opportunities
    "Opportunity", "OpportunityStage", "OpportunityType",
    "OpportunityProduct",
    "Quotation", "QuotationStatus", "QuotationItem",
 
    # System
    "AuditLog", "AuditAction",
    "Notification", "NotificationType",
    
    
    # Activity & Documents
    "TimelineActivity", "Document"
]