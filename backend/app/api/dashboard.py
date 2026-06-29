from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import SessionLocal
from app.models import Account, Contact, Lead, Opportunity
from app.core.rbac import require_permission
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    accounts_count = db.query(Account).filter(Account.is_deleted == False).count()
    contacts_count = db.query(Contact).filter(Contact.is_deleted == False).count()
    leads_count = db.query(Lead).filter(Lead.is_deleted == False).count()
    opportunities_count = db.query(Opportunity).filter(Opportunity.is_deleted == False).count()
    
    # Calculate revenue from WON opportunities, fallback to just summing amounts if stage enum differs
    revenue_val = db.query(func.sum(Opportunity.amount)).filter(
        Opportunity.is_deleted == False,
        Opportunity.stage == "closed_won"
    ).scalar()
    
    revenue = float(revenue_val) if revenue_val else 0.0

    return {
        "accounts": accounts_count,
        "contacts": contacts_count,
        "leads": leads_count,
        "opportunities": opportunities_count,
        "revenue": revenue
    }
