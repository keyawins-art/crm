from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    INVITED = "invited"


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    # Basic Info
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)

    # Auth
    hashed_password = Column(String(255), nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)

    # Status
    status = Column(SAEnum(UserStatus), default=UserStatus.INVITED, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(String(50), nullable=True)  # ISO datetime string

    # RBAC — har user ka ek role hoga
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Profile
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="Asia/Kolkata", nullable=False)
    language = Column(String(10), default="en", nullable=False)

    role = relationship("Role", back_populates="users", lazy="joined")

    assigned_leads = relationship("Lead", back_populates="assigned_to", lazy="dynamic",
                                  foreign_keys="Lead.assigned_to_id")
    assigned_opportunities = relationship("Opportunity", back_populates="assigned_to", lazy="dynamic",
                                          foreign_keys="Opportunity.assigned_to_id")
    activities = relationship("AuditLog", back_populates="user", lazy="dynamic")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"