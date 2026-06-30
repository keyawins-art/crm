import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.integration import IntegrationConfig, IntegrationProvider, IntegrationStatus

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Manager to orchestrate and simulate external integrations."""
    
    @staticmethod
    def _is_active(db: Session, provider: IntegrationProvider) -> bool:
        config = db.query(IntegrationConfig).filter(IntegrationConfig.provider_name == provider).first()
        return config is not None and config.is_enabled

    @classmethod
    def send_email(cls, db: Session, provider: IntegrationProvider, to_email: str, subject: str, body: str) -> dict:
        if not cls._is_active(db, provider):
            logger.warning(f"Integration {provider} is not active. Skipping.")
            return {"status": "skipped", "reason": "disabled"}

        # Simulate API call
        logger.info(f"[{provider.upper()} INTEGRATION] Sending email to {to_email}. Subject: {subject}")
        return {
            "status": "success",
            "provider": provider.value,
            "message_id": f"mock-{provider.value}-{datetime.now().timestamp()}",
            "details": f"Email sent to {to_email}"
        }

    @classmethod
    def send_sms_or_whatsapp(cls, db: Session, provider: IntegrationProvider, phone: str, message: str) -> dict:
        if not cls._is_active(db, provider):
            logger.warning(f"Integration {provider} is not active. Skipping.")
            return {"status": "skipped", "reason": "disabled"}

        # Simulate API call
        logger.info(f"[{provider.upper()} INTEGRATION] Sending message to {phone}: {message}")
        return {
            "status": "success",
            "provider": provider.value,
            "message_id": f"mock-{provider.value}-{datetime.now().timestamp()}",
            "details": f"Message sent to {phone}"
        }

    @classmethod
    def sync_meeting(cls, db: Session, provider: IntegrationProvider, subject: str, description: str, start_time: datetime, end_time: datetime) -> dict:
        if not cls._is_active(db, provider):
            logger.warning(f"Integration {provider} is not active. Skipping.")
            return {"status": "skipped", "reason": "disabled"}

        # Simulate API Sync
        logger.info(f"[{provider.upper()} INTEGRATION] Syncing event '{subject}' for {start_time} - {end_time}")
        return {
            "status": "success",
            "provider": provider.value,
            "event_id": f"mock-cal-{provider.value}-{datetime.now().timestamp()}",
            "details": f"Meeting '{subject}' synced successfully"
        }

    @classmethod
    def process_payment(cls, db: Session, provider: IntegrationProvider, amount: float, currency: str = "INR") -> dict:
        if not cls._is_active(db, provider):
            logger.warning(f"Integration {provider} is not active. Skipping.")
            return {"status": "skipped", "reason": "disabled"}

        # Simulate checkout/charge
        logger.info(f"[{provider.upper()} INTEGRATION] Processing payment of {amount} {currency}")
        return {
            "status": "success",
            "provider": provider.value,
            "transaction_id": f"txn-{provider.value}-{datetime.now().timestamp()}",
            "amount": amount,
            "currency": currency,
            "details": "Charge succeeded"
        }
