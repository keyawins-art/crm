from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin


class KnowledgeBaseArticle(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "kb_articles"

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=list, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author = relationship("User", lazy="joined")

    def __repr__(self):
        return f"<KnowledgeBaseArticle '{self.title}' (Published: {self.is_published})>"
