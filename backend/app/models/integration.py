import enum
from sqlalchemy import Column, String, Boolean, Enum as SAEnum, Text
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
    # Stores Fernet-encrypted JSON blob — never plaintext secrets
    credentials_encrypted = Column("credentials", Text, nullable=True)
    status = Column(SAEnum(IntegrationStatus), default=IntegrationStatus.DISCONNECTED, nullable=False)

    # ---- helpers for transparent encrypt / decrypt ----

    def set_credentials(self, data: dict) -> None:
        """Encrypt and store credentials."""
        from app.core.crypto import encrypt_json_safe
        self.credentials_encrypted = encrypt_json_safe(data)

    def get_credentials(self) -> dict:
        """Decrypt and return credentials."""
        from app.core.crypto import decrypt_json_safe
        return decrypt_json_safe(self.credentials_encrypted)

    def __repr__(self):
        return f"<IntegrationConfig {self.provider_name} [{self.status}]>"
