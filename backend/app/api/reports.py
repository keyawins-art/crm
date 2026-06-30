from typing import List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from fastapi import APIRouter, Depends

from app.db.database import SessionLocal
from app.models.user import User
from app.models.lead import Lead, LeadStatus
from app.models.opportunity import Opportunity, OpportunityStage
from app.core.rbac import require_permission

router = APIRouter(prefix="/crm/reports", tags=["Reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def apply_rls(query, current_user, model):
    """Apply Row-Level Security based on user role."""
    if current_user.role and current_user.role.name == "Sales Executive":
        # Assuming model has assigned_to_id or owner_id
        if hasattr(model, 'owner_id'):
            query = query.filter(model.owner_id == current_user.id)
        elif hasattr(model, 'assigned_to_id'):
            query = query.filter(model.assigned_to_id == current_user.id)
    return query

@router.get("/sales")
def get_sales_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities:read"))
):
    """Group opportunities by stage to show the active pipeline."""
    query = db.query(
        Opportunity.stage,
        func.count(Opportunity.id).label("count"),
        func.sum(Opportunity.amount).label("total_amount")
    ).filter(Opportunity.is_deleted == False)
    
    query = apply_rls(query, current_user, Opportunity)
    
    results = query.group_by(Opportunity.stage).all()
    
    return [
        {
            "stage": result.stage.value if hasattr(result.stage, 'value') else result.stage,
            "count": result.count,
            "total_amount": float(result.total_amount or 0)
        }
        for result in results
    ]

@router.get("/revenue")
def get_revenue_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities:read"))
):
    """Show CLOSED_WON revenue grouped by month for the current year."""
    current_year = datetime.now().year
    
    query = db.query(
        extract('month', Opportunity.close_date).label("month"),
        func.sum(Opportunity.amount).label("revenue")
    ).filter(
        Opportunity.is_deleted == False,
        Opportunity.stage == OpportunityStage.CLOSED_WON,
        extract('year', Opportunity.close_date) == current_year
    )
    
    query = apply_rls(query, current_user, Opportunity)
    
    results = query.group_by("month").order_by("month").all()
    
    # Format months (1=Jan, 2=Feb, etc)
    months_map = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
    
    return [
        {
            "month": months_map.get(int(result.month), str(result.month)),
            "revenue": float(result.revenue or 0)
        }
        for result in results
    ]

@router.get("/leads/funnel")
def get_lead_funnel(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("leads:read"))
):
    """Group leads by status to visualize the funnel."""
    query = db.query(
        Lead.status,
        func.count(Lead.id).label("count")
    ).filter(Lead.is_deleted == False)
    
    query = apply_rls(query, current_user, Lead)
    
    results = query.group_by(Lead.status).all()
    
    return [
        {
            "status": result.status.value if hasattr(result.status, 'value') else result.status,
            "count": result.count
        }
        for result in results
    ]

@router.get("/leads/conversion")
def get_lead_conversion_rate(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("leads:read"))
):
    """Calculate the conversion rate of leads."""
    base_query = db.query(Lead).filter(Lead.is_deleted == False)
    base_query = apply_rls(base_query, current_user, Lead)
    
    total_leads = base_query.count()
    
    if total_leads == 0:
        return {"total_leads": 0, "converted_leads": 0, "conversion_rate_percentage": 0.0}
        
    converted_leads = base_query.filter(Lead.is_converted == True).count()
    
    return {
        "total_leads": total_leads,
        "converted_leads": converted_leads,
        "conversion_rate_percentage": round((converted_leads / total_leads) * 100, 2)
    }

@router.get("/performance")
def get_performance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities:read"))
):
    """Leaderboard of Sales Executives by Closed Won Revenue."""
    query = db.query(
        User.first_name,
        User.last_name,
        func.sum(Opportunity.amount).label("total_revenue"),
        func.count(Opportunity.id).label("deals_closed")
    ).join(
        Opportunity, User.id == Opportunity.assigned_to_id
    ).filter(
        Opportunity.is_deleted == False,
        Opportunity.stage == OpportunityStage.CLOSED_WON
    )
    
    # If a Sales Exec requests this, they only see themselves. Admin sees all.
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(User.id == current_user.id)
        
    results = query.group_by(User.id).order_by(func.sum(Opportunity.amount).desc()).all()
    
    return [
        {
            "sales_executive": f"{result.first_name} {result.last_name or ''}".strip(),
            "total_revenue": float(result.total_revenue or 0),
            "deals_closed": result.deals_closed
        }
        for result in results
    ]

@router.get("/leads")
def get_leads_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("leads:read"))
):
    """General report for Leads grouped by status and rating."""
    query = db.query(Lead).filter(Lead.is_deleted == False)
    query = apply_rls(query, current_user, Lead)
    
    total = query.count()
    converted = query.filter(Lead.is_converted == True).count()
    hot_leads = query.filter(Lead.rating == "hot").count()
    
    return {
        "total_leads": total,
        "converted_leads": converted,
        "hot_leads": hot_leads,
        "conversion_rate": round((converted / total * 100) if total > 0 else 0, 2)
    }

@router.get("/opportunities")
def get_opportunities_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities:read"))
):
    """General report for Opportunities showing pipeline health."""
    query = db.query(Opportunity).filter(Opportunity.is_deleted == False)
    query = apply_rls(query, current_user, Opportunity)
    
    total = query.count()
    won = query.filter(Opportunity.stage == OpportunityStage.CLOSED_WON).count()
    lost = query.filter(Opportunity.stage == OpportunityStage.CLOSED_LOST).count()
    open_opps = total - won - lost
    
    from sqlalchemy.sql import func
    total_value = db.query(func.sum(Opportunity.amount)).filter(Opportunity.is_deleted == False).scalar() or 0
    won_value = db.query(func.sum(Opportunity.amount)).filter(Opportunity.is_deleted == False, Opportunity.stage == OpportunityStage.CLOSED_WON).scalar() or 0
    
    return {
        "total_opportunities": total,
        "open_opportunities": open_opps,
        "won_opportunities": won,
        "lost_opportunities": lost,
        "total_pipeline_value": float(total_value),
        "won_revenue": float(won_value)
    }

@router.get("/users")
def get_users_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities:read"))
):
    """Report of activity and load per user."""
    from sqlalchemy.sql import func
    
    # Get active users
    users = db.query(User).filter(User.is_active == True).all()
    report = []
    
    for u in users:
        leads_count = db.query(Lead).filter(Lead.assigned_to_id == u.id, Lead.is_deleted == False).count() if hasattr(Lead, 'assigned_to_id') else 0
        opps_count = db.query(Opportunity).filter(Opportunity.assigned_to_id == u.id, Opportunity.is_deleted == False).count()
        won_revenue = db.query(func.sum(Opportunity.amount)).filter(
            Opportunity.assigned_to_id == u.id, 
            Opportunity.stage == OpportunityStage.CLOSED_WON,
            Opportunity.is_deleted == False
        ).scalar() or 0
        
        report.append({
            "user_id": u.id,
            "name": f"{u.first_name} {u.last_name or ''}".strip(),
            "role": u.role.name if u.role else "N/A",
            "active_leads": leads_count,
            "active_opportunities": opps_count,
            "won_revenue": float(won_revenue)
        })
        
    return sorted(report, key=lambda x: x["won_revenue"], reverse=True)


@router.get("/charts/lead-sources")
def get_chart_lead_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("leads:read"))
):
    """Chart data for Lead Sources pie chart."""
    from app.models.lead import LeadSource
    
    query = db.query(
        LeadSource.name,
        func.count(Lead.id).label("count")
    ).outerjoin(
        Lead, Lead.source_id == LeadSource.id
    ).filter(Lead.is_deleted == False)
    
    query = apply_rls(query, current_user, Lead)
    results = query.group_by(LeadSource.name).all()
    
    return [
        {"source": result.name, "count": result.count}
        for result in results
    ]


@router.get("/charts/win-loss")
def get_chart_win_loss(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("opportunities:read"))
):
    """Chart data for Win/Loss ratio."""
    query = db.query(Opportunity).filter(Opportunity.is_deleted == False)
    query = apply_rls(query, current_user, Opportunity)
    
    won = query.filter(Opportunity.stage == OpportunityStage.CLOSED_WON).count()
    lost = query.filter(Opportunity.stage == OpportunityStage.CLOSED_LOST).count()
    
    total_closed = won + lost
    win_rate = round((won / total_closed * 100) if total_closed > 0 else 0, 2)
    loss_rate = round((lost / total_closed * 100) if total_closed > 0 else 0, 2)
    
    return {
        "won": won,
        "lost": lost,
        "win_rate_percentage": win_rate,
        "loss_rate_percentage": loss_rate
    }
