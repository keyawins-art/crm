from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


# ─── Enums ────────────────────────────────────────────────────────────────────

class LeadSourceType(str, enum.Enum):
    WEBSITE = "website"
    COLD_CALL = "cold_call"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    TRADE_SHOW = "trade_show"
    ADVERTISEMENT = "advertisement"
    PARTNER = "partner"
    OTHER = "other"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROCESS = "in_process"
    CONVERTED = "converted"
    RECYCLED = "recycled"
    DEAD = "dead"


class LeadRating(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ActivityType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    DEMO = "demo"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class ActivityOutcome(str, enum.Enum):
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    CALLBACK = "callback"
    NO_ANSWER = "no_answer"
    LEFT_MESSAGE = "left_message"
    OTHER = "other"


# ─── Models ───────────────────────────────────────────────────────────────────

class LeadSource(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lead_sources"

    name = Column(String(100), unique=True, nullable=False)
    type = Column(SAEnum(LeadSourceType), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    leads = relationship("Lead", back_populates="source", lazy="dynamic")

    def __repr__(self):
        return f"<LeadSource {self.name}>"


class Lead(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    # Identity
    salutation = Column(String(10), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company = Column(String(255), nullable=True)
    title = Column(String(100), nullable=True)

    # Contact Info
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)

    # Status
    status = Column(SAEnum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True)
    rating = Column(SAEnum(LeadRating), nullable=True)

    # Qualification
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    no_of_employees = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Conversion tracking
    is_converted = Column(Boolean, default=False, nullable=False, index=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    converted_account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    converted_contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    converted_opportunity_id = Column(UUID(as_uuid=True), nullable=True)  # populated after opportunity created

    # Foreign Keys
    source_id = Column(UUID(as_uuid=True), ForeignKey("lead_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    source = relationship("LeadSource", back_populates="leads", lazy="joined")
    account = relationship("Account", back_populates="leads", foreign_keys=[account_id], lazy="joined")
    contact = relationship("Contact", back_populates="leads", foreign_keys=[contact_id], lazy="joined")
    assigned_to = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to_id], lazy="joined")
    created_by = relationship("User", foreign_keys=[created_by_id], lazy="joined")
    activities = relationship("LeadActivity", back_populates="lead", lazy="dynamic", cascade="all, delete-orphan")
    notes = relationship("LeadNote", back_populates="lead", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Lead {self.full_name} [{self.status}]>"


class LeadActivity(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lead_activities"

    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    type = Column(SAEnum(ActivityType), nullable=False)
    outcome = Column(SAEnum(ActivityOutcome), nullable=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    activity_date = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(String(10), nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="activities")
    user = relationship("User", lazy="joined")

    def __repr__(self):
        return f"<LeadActivity {self.type} on Lead {self.lead_id}>"


class LeadNote(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "lead_notes"

    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="notes")
    user = relationship("User", lazy="joined")

    def __repr__(self):
        return f"<LeadNote on Lead {self.lead_id}>"