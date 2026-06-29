from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import SessionLocal
from app.models.audit import Notification, NotificationType
from app.models.user import User
from app.models.activity import TimelineActivity, ActivityType
from app.core.rbac import require_permission
from app.schemas.notification import NotificationRead
from app.schemas.crm import PaginatedResponse

router = APIRouter(tags=["Notifications"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def send_notification(db: Session, user_id: UUID, title: str, message: str, type: NotificationType = NotificationType.INFO):
    if not user_id:
        return None
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=type
    )
    db.add(notif)
    db.flush()
    return notif

@router.get("/notifications", response_model=PaginatedResponse[NotificationRead])
def list_notifications(
    current_user: User = Depends(require_permission("accounts:read")), # Base permission
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 20,
    unread_only: bool = False
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_deleted == False)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
        
    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(Notification.created_at.desc()).offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }

@router.post("/notifications/read-all", status_code=status.HTTP_200_OK)
def mark_all_read(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).update({"is_read": True, "read_at": func.now()})
    db.commit()
    return {"status": "success"}

@router.post("/notifications/{id}/read", response_model=NotificationRead)
def mark_read(
    id: UUID,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.id == id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    if not notif.is_read:
        notif.is_read = True
        notif.read_at = func.now()
        db.commit()
        db.refresh(notif)
        
    return notif

# System cron endpoint to trigger time-based reminders
@router.post("/system/trigger-reminders", status_code=status.HTTP_200_OK)
def trigger_reminders(db: Session = Depends(get_db)):
    # Find all meetings or tasks due in the next 24 hours that haven't been notified yet.
    # To keep it simple, we use a naive approach: check activities from now to next 24h.
    # We rely on searching Notification table to ensure we don't spam.
    
    now = datetime.utcnow()
    next_24h = now + timedelta(hours=24)
    
    # We consider Call, Email, Meeting as "Tasks/Meetings" with due dates if activity_date is future.
    upcoming_activities = db.query(TimelineActivity).filter(
        TimelineActivity.activity_date > now,
        TimelineActivity.activity_date <= next_24h,
        TimelineActivity.user_id.isnot(None)
    ).all()
    
    notified_count = 0
    for act in upcoming_activities:
        # Check if a notification already exists for this activity to prevent spam
        # We can use the entity_id or title trick, but ideally we'd have a tracking table.
        # We'll check if a notification with title starting with "Reminder:" for this act id exists.
        
        # A lightweight way to track is just search existing notifications
        exists = db.query(Notification).filter(
            Notification.user_id == act.user_id,
            Notification.title.like(f"Reminder: Upcoming {act.activity_type}%")
        ).first() # Very naive deduplication for this phase
        
        if not exists:
            msg = f"You have an upcoming {act.activity_type.value.lower()} scheduled for {act.activity_date.strftime('%Y-%m-%d %H:%M')} regarding {act.entity_type}."
            send_notification(
                db=db,
                user_id=act.user_id,
                title=f"Reminder: Upcoming {act.activity_type.value}",
                message=msg,
                type=NotificationType.INFO
            )
            notified_count += 1
            
    db.commit()
    return {"status": "success", "triggered": notified_count}
