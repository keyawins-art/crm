from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, or_, case

from app.db.database import SessionLocal
from app.models import Account, Contact, Lead, Opportunity
from app.models.lead import LeadStatus, LeadRating
from app.models.opportunity import OpportunityStage
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


from app.models.audit import AuditLog

@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("accounts:read")),
    limit: int = 50
):
    # Only Admin sees all logs. Sales Exec sees their own logs.
    query = db.query(AuditLog)
    if current_user.role and current_user.role.name != "Admin":
        query = query.filter(AuditLog.user_id == current_user.id)
        
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at,
            "user": {
                "first_name": log.user.first_name if log.user else "System",
                "last_name": log.user.last_name if log.user else ""
            }
        }
        for log in logs
    ]


# ─── Smart Dashboard ──────────────────────────────────────────────────────────

from datetime import date, datetime, timedelta

def _apply_rls(query, current_user, model):
    """Row-level security: Sales Executives see only their own records."""
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(model, "assigned_to_id"):
            query = query.filter(model.assigned_to_id == current_user.id)
    return query


@router.get("/smart")
def get_smart_dashboard(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
):
    """Single endpoint powering all 4 smart dashboard widgets."""
    today = date.today()
    current_year = today.year
    is_admin = current_user.role and current_user.role.name != "Sales Executive"

    # ── 1. Overdue Follow-ups ──────────────────────────────────────────────
    overdue_q = (
        db.query(Lead)
        .filter(
            Lead.is_deleted == False,
            Lead.next_followup_date != None,
            Lead.next_followup_date < datetime.now(),
            Lead.status.notin_([LeadStatus.CONVERTED, LeadStatus.DEAD]),
        )
    )
    overdue_q = _apply_rls(overdue_q, current_user, Lead)
    overdue_leads = overdue_q.order_by(Lead.next_followup_date.asc()).limit(15).all()

    overdue_followups = []
    for lead in overdue_leads:
        days = (today - lead.next_followup_date.date()).days if lead.next_followup_date else 0
        overdue_followups.append({
            "id": str(lead.id),
            "name": lead.full_name,
            "company": lead.company or "—",
            "rating": lead.rating.value if lead.rating else None,
            "days_overdue": days,
            "followup_date": lead.next_followup_date.isoformat() if lead.next_followup_date else None,
            "assigned_to": lead.assigned_to.full_name if lead.assigned_to else "Unassigned",
            "phone": lead.phone or lead.mobile or None,
        })

    # ── 2. Target vs Achievement (monthly, current year) ──────────────────
    monthly_rev_q = (
        db.query(
            extract("month", Opportunity.close_date).label("month"),
            func.sum(Opportunity.amount).label("revenue"),
        )
        .filter(
            Opportunity.is_deleted == False,
            Opportunity.stage == OpportunityStage.CLOSED_WON,
            extract("year", Opportunity.close_date) == current_year,
        )
    )
    monthly_rev_q = _apply_rls(monthly_rev_q, current_user, Opportunity)
    monthly_rev = monthly_rev_q.group_by("month").order_by("month").all()

    months_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
    }

    rev_by_month = {int(r.month): float(r.revenue or 0) for r in monthly_rev}
    past_months = [v for m, v in rev_by_month.items() if m <= today.month and v > 0]
    avg_rev = sum(past_months) / len(past_months) if past_months else 0
    monthly_target = round(avg_rev * 1.2, 2)

    target_vs_achievement = []
    for m in range(1, 13):
        target_vs_achievement.append({
            "month": months_map[m],
            "achievement": rev_by_month.get(m, 0),
            "target": monthly_target,
        })

    # ── 3. Sales-person Performance ───────────────────────────────────────
    users_q = db.query(User).filter(User.is_active == True)
    if not is_admin:
        users_q = users_q.filter(User.id == current_user.id)
    users = users_q.all()

    salesperson_performance = []
    for u in users:
        # Won revenue & deals
        won_q = (
            db.query(
                func.coalesce(func.sum(Opportunity.amount), 0).label("won_rev"),
                func.count(Opportunity.id).label("deals_won"),
            )
            .filter(
                Opportunity.assigned_to_id == u.id,
                Opportunity.is_deleted == False,
                Opportunity.stage == OpportunityStage.CLOSED_WON,
            )
        )
        won_row = won_q.first()

        # Active pipeline value
        pipeline_val = (
            db.query(func.coalesce(func.sum(Opportunity.amount), 0))
            .filter(
                Opportunity.assigned_to_id == u.id,
                Opportunity.is_deleted == False,
                Opportunity.stage.notin_([OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]),
            )
            .scalar()
        )

        # Lead stats
        total_leads = (
            db.query(func.count(Lead.id))
            .filter(Lead.assigned_to_id == u.id, Lead.is_deleted == False)
            .scalar()
        )
        converted_leads = (
            db.query(func.count(Lead.id))
            .filter(Lead.assigned_to_id == u.id, Lead.is_deleted == False, Lead.is_converted == True)
            .scalar()
        )
        conversion_rate = round((converted_leads / total_leads * 100) if total_leads > 0 else 0, 1)

        salesperson_performance.append({
            "name": u.full_name,
            "email": u.email,
            "won_revenue": float(won_row.won_rev) if won_row else 0,
            "deals_won": won_row.deals_won if won_row else 0,
            "pipeline_value": float(pipeline_val or 0),
            "total_leads": total_leads or 0,
            "converted_leads": converted_leads or 0,
            "conversion_rate": conversion_rate,
        })

    salesperson_performance.sort(key=lambda x: x["won_revenue"], reverse=True)

    # ── 4. Revenue Forecast (next 3 months, weighted) ─────────────────────
    forecast_start = today.replace(day=1)
    forecast_end_month = today.month + 3
    forecast_end_year = current_year
    if forecast_end_month > 12:
        forecast_end_month -= 12
        forecast_end_year += 1
    forecast_end = date(forecast_end_year, forecast_end_month, 1)

    weighted_q = (
        db.query(
            extract("month", Opportunity.close_date).label("month"),
            extract("year", Opportunity.close_date).label("year"),
            func.sum(Opportunity.amount * Opportunity.probability / 100).label("weighted"),
            func.sum(Opportunity.amount).label("total_pipeline"),
            func.count(Opportunity.id).label("deal_count"),
        )
        .filter(
            Opportunity.is_deleted == False,
            Opportunity.stage.notin_([OpportunityStage.CLOSED_WON, OpportunityStage.CLOSED_LOST]),
            Opportunity.close_date >= forecast_start,
            Opportunity.close_date < forecast_end,
        )
    )
    weighted_q = _apply_rls(weighted_q, current_user, Opportunity)
    weighted_rows = weighted_q.group_by("year", "month").order_by("year", "month").all()

    # Current month actual
    current_month_actual = rev_by_month.get(today.month, 0)

    revenue_forecast = []
    for row in weighted_rows:
        m = int(row.month)
        y = int(row.year)
        is_current = m == today.month and y == current_year
        revenue_forecast.append({
            "month": months_map.get(m, str(m)),
            "year": y,
            "weighted_forecast": round(float(row.weighted or 0), 2),
            "total_pipeline": round(float(row.total_pipeline or 0), 2),
            "deal_count": row.deal_count,
            "actual": current_month_actual if is_current else 0,
        })

    # If no forecast rows but we have current month data, include it
    if not revenue_forecast and current_month_actual > 0:
        revenue_forecast.append({
            "month": months_map[today.month],
            "year": current_year,
            "weighted_forecast": 0,
            "total_pipeline": 0,
            "deal_count": 0,
            "actual": current_month_actual,
        })

    return {
        "overdue_followups": overdue_followups,
        "target_vs_achievement": target_vs_achievement,
        "salesperson_performance": salesperson_performance,
        "revenue_forecast": revenue_forecast,
    }

