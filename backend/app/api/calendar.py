from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import SessionLocal
from app.core.rbac import require_permission
from app.models.user import User
from app.models.task import Task
from app.models.meeting import Meeting
from app.models.call import Call
from app.schemas.calendar import CalendarEvent

router = APIRouter(prefix="/crm/calendar", tags=["Calendar"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=List[CalendarEvent])
def get_calendar(
    current_user: User = Depends(require_permission("leads:read")), # Base CRM permission
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None, description="Start date for calendar view"),
    end_date: Optional[datetime] = Query(None, description="End date for calendar view")
):
    events = []
    
    # Base filter for RLS (Sales Executives only see their own items)
    is_sales_exec = current_user.role and current_user.role.name == "Sales Executive"
    
    # 1. Fetch Tasks
    task_query = db.query(Task).filter(Task.is_deleted == False, Task.due_date.isnot(None))
    if is_sales_exec:
        task_query = task_query.filter(or_(Task.assigned_to_id == current_user.id, Task.created_by_id == current_user.id))
    if start_date:
        task_query = task_query.filter(Task.due_date >= start_date)
    if end_date:
        task_query = task_query.filter(Task.due_date <= end_date)
        
    for task in task_query.all():
        events.append(CalendarEvent(
            id=task.id,
            type="task",
            title=task.title,
            start_time=task.due_date,
            end_time=None,
            status=task.status.value,
            lead_id=task.lead_id,
            contact_id=task.contact_id,
            opportunity_id=task.opportunity_id
        ))
        
    # 2. Fetch Meetings
    meeting_query = db.query(Meeting).filter(Meeting.is_deleted == False)
    if is_sales_exec:
        meeting_query = meeting_query.filter(Meeting.created_by_id == current_user.id)
    if start_date:
        meeting_query = meeting_query.filter(Meeting.start_time >= start_date)
    if end_date:
        meeting_query = meeting_query.filter(Meeting.end_time <= end_date)
        
    for meet in meeting_query.all():
        events.append(CalendarEvent(
            id=meet.id,
            type="meeting",
            title=meet.subject,
            start_time=meet.start_time,
            end_time=meet.end_time,
            status=meet.status.value,
            lead_id=meet.lead_id,
            contact_id=meet.contact_id,
            opportunity_id=meet.opportunity_id
        ))

    # 3. Fetch Calls (Follow-ups)
    call_query = db.query(Call).filter(Call.is_deleted == False, Call.follow_up_date.isnot(None))
    if is_sales_exec:
        call_query = call_query.filter(Call.created_by_id == current_user.id)
    if start_date:
        call_query = call_query.filter(Call.follow_up_date >= start_date)
    if end_date:
        call_query = call_query.filter(Call.follow_up_date <= end_date)
        
    for call in call_query.all():
        events.append(CalendarEvent(
            id=call.id,
            type="call",
            title=f"Follow-up: {call.phone_number}",
            start_time=call.follow_up_date,
            end_time=None,
            status="pending" if call.follow_up_date > datetime.now(timezone.utc) else "overdue",
            lead_id=call.lead_id,
            contact_id=call.contact_id,
            opportunity_id=call.opportunity_id
        ))
        
    # Sort all events chronologically
    events.sort(key=lambda e: e.start_time)
    
    return events
