from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from .base import Base, UUIDMixin, TimestampMixin

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    INVITED = "invited"


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    # Basic Info
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)

    # Auth
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # RBAC — har user ka ek role hoga
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    role = relationship("Role", back_populates="users", lazy="selectin")

    assigned_leads = relationship("Lead", back_populates="assigned_to", lazy="dynamic",
                                  foreign_keys="Lead.assigned_to_id")
    assigned_opportunities = relationship("Opportunity", back_populates="assigned_to", lazy="dynamic",
                                          foreign_keys="Opportunity.assigned_to_id")
    activities = relationship("AuditLog", back_populates="user", lazy="dynamic")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def status(self):
        return UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE

    @status.setter
    def status(self, value):
        self.is_active = value == UserStatus.ACTIVE

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"