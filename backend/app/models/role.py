from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True)

    description = Column(Text, nullable=True)

    # Relationships
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin"
    )
    users = relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False, index=True)

    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False)  
    action = Column(String(50), nullable=False)    

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    # Relationships
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission {self.name}>"


class RolePermission(Base):
    """Many-to-many join table between Role and Permission."""
    __tablename__ = "role_permissions"

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    )
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True
    )