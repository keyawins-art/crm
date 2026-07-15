"""
Token blacklist model for JWT revocation.

When a user logs out (or an admin force-revokes a session), the token's ``jti``
claim is inserted here. ``get_current_user`` checks this table before trusting
the token.

Expired entries can be cleaned up periodically since the JWT itself would
fail expiry validation anyway.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, UUIDMixin


class BlacklistedToken(Base, UUIDMixin):
    __tablename__ = "blacklisted_tokens"

    # The unique JWT ID (jti claim) — this is what we look up
    jti = Column(String(36), unique=True, nullable=False, index=True)

    # Which user this token belonged to (optional FK for auditing)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    # When the token naturally expires — allows periodic cleanup
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # When it was blacklisted
    blacklisted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Index for cleanup queries
    __table_args__ = (
        Index("ix_blacklisted_tokens_expires_at", "expires_at"),
    )

    def __repr__(self):
        return f"<BlacklistedToken jti={self.jti}>"
