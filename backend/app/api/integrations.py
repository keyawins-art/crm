from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.models.integration import IntegrationConfig, IntegrationProvider, IntegrationStatus
from app.core.rbac import require_permission
from app.schemas.integration import IntegrationConfigRead, IntegrationConnect
from app.core.integrations.manager import IntegrationManager

router = APIRouter(prefix="/crm/integrations", tags=["Integrations"])

def get_db():
    db = SessionLocal()
    try:
        db_configs = db.query(IntegrationConfig).all()
        # Seed all providers if they don't exist yet
        existing = {c.provider_name for c in db_configs}
        for provider in IntegrationProvider:
            if provider not in existing:
                new_conf = IntegrationConfig(
                    provider_name=provider,
                    is_enabled=False,
                    status=IntegrationStatus.DISCONNECTED,
                    credentials={}
                )
                db.add(new_conf)
        db.commit()
        yield db
    finally:
        db.close()


@router.get("", response_model=List[IntegrationConfigRead])
def list_integrations(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    """List all integrations and their current configurations."""
    return db.query(IntegrationConfig).all()


@router.post("/{provider}/connect", response_model=IntegrationConfigRead)
def connect_integration(
    provider: IntegrationProvider,
    payload: IntegrationConnect,
    current_user: User = Depends(require_permission("accounts:read")), # Allowed for user who can read accounts
    db: Session = Depends(get_db)
):
    """Enable and connect an integration with credentials."""
    config = db.query(IntegrationConfig).filter(IntegrationConfig.provider_name == provider).first()
    if not config:
        raise HTTPException(status_code=404, detail="Integration provider not found")
        
    config.set_credentials(payload.credentials)
    config.is_enabled = True
    config.status = IntegrationStatus.CONNECTED
    db.commit()
    db.refresh(config)
    return config


@router.post("/{provider}/disconnect", response_model=IntegrationConfigRead)
def disconnect_integration(
    provider: IntegrationProvider,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    """Disable and disconnect an integration."""
    config = db.query(IntegrationConfig).filter(IntegrationConfig.provider_name == provider).first()
    if not config:
        raise HTTPException(status_code=404, detail="Integration provider not found")
        
    config.is_enabled = False
    config.status = IntegrationStatus.DISCONNECTED
    db.commit()
    db.refresh(config)
    return config


@router.post("/{provider}/test")
def test_integration(
    provider: IntegrationProvider,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    """Run a test action for the integration."""
    config = db.query(IntegrationConfig).filter(IntegrationConfig.provider_name == provider).first()
    if not config or not config.is_enabled:
        raise HTTPException(status_code=400, detail=f"Integration {provider} is not active. Please connect it first.")

    # Call manager to run test
    if provider in [IntegrationProvider.GMAIL, IntegrationProvider.OUTLOOK]:
        res = IntegrationManager.send_email(db, provider, "test@example.com", "Test Subject", "Test Body")
    elif provider in [IntegrationProvider.TWILIO, IntegrationProvider.WHATSAPP]:
        res = IntegrationManager.send_sms_or_whatsapp(db, provider, "+1234567890", "Test message from CRM")
    elif provider in [IntegrationProvider.STRIPE, IntegrationProvider.RAZORPAY]:
        res = IntegrationManager.process_payment(db, provider, 1000.0)
    elif provider in [IntegrationProvider.GOOGLE_CALENDAR, IntegrationProvider.OFFICE365]:
        import datetime
        res = IntegrationManager.sync_meeting(db, provider, "Test Meeting", "Desc", datetime.datetime.now(), datetime.datetime.now())
    else:
        res = {"status": "error", "message": "Unknown provider type"}

    return {"status": "success", "provider": provider.value, "result": res}
