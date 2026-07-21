from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin

class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    entity_type = Column(String(50), nullable=False, index=True) # e.g. "accounts", "quotations"
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False) # In bytes
    category = Column(String(100), nullable=True) # e.g. "GST Certificate", "Invoice"
    
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    uploaded_by = relationship("User", lazy="joined")

    @property
    def download_url(self):
        return f"/crm/documents/{self.id}/download"

    def __repr__(self):
        return f"<Document {self.filename} for {self.entity_type}/{self.entity_id}>"
