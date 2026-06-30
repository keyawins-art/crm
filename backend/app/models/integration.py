import enum
from sqlalchemy import Column, String, Boolean, Enum as SAEnum, JSON
from .base import Base, UUIDMixin, TimestampMixin


class IntegrationProvider(str, enum.Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    WHATSAPP = "whatsapp"
    TWILIO = "twilio"
    STRIPE = "stripe"
    RAZORPAY = "razorpay"
    GOOGLE_CALENDAR = "google_calendar"
    OFFICE365 = "office365"


class IntegrationStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class IntegrationConfig(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "integration_configs"

    provider_name = Column(SAEnum(IntegrationProvider), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
    credentials = Column(JSON, nullable=False, default=dict) # Securely stores tokens/secrets
    status = Column(SAEnum(IntegrationStatus), default=IntegrationStatus.DISCONNECTED, nullable=False)

    def __repr__(self):
        return f"<IntegrationConfig {self.provider_name} [{self.status}]>"
