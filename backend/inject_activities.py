with open('app/api/crm.py', 'r') as f:
    content = f.read()

# Make sure imports are present
if "TimelineActivity" not in content:
    content = content.replace("from app.models import (", "from app.models.activity import TimelineActivity\nfrom app.models import (")

if "ActivityCreate" not in content:
    content = "from app.schemas.activity import ActivityCreate, ActivityRead\n" + content

activity_endpoints = """
# Activity Timeline
@router.post("/{module_name}/{id}/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    module_name: str,
    id: UUID,
    payload: ActivityCreate,
    current_user: User = Depends(require_permission("accounts:read")), # Must have basic read access
    db: Session = Depends(get_db),
):
    from sqlalchemy.sql import func
    # Validate that module_name is valid
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations"]
    if module_name not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid module name")
        
    activity = TimelineActivity(
        entity_type=module_name,
        entity_id=id,
        activity_type=payload.activity_type,
        content=payload.content,
        activity_date=payload.activity_date or func.now(),
        user_id=current_user.id
    )
    db.add(activity)
    
    # We log this creation to audit logs too
    log_audit(db, current_user, AuditAction.CREATED, "Activity", id)
    
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/{module_name}/{id}/activities", response_model=PaginatedResponse[ActivityRead])
def list_activities(
    module_name: str,
    id: UUID,
    request: Request,
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    valid_modules = ["accounts", "contacts", "leads", "opportunities", "products", "quotations"]
    if module_name not in valid_modules:
        raise HTTPException(status_code=400, detail="Invalid module name")
        
    query = db.query(TimelineActivity).filter(
        TimelineActivity.entity_type == module_name,
        TimelineActivity.entity_id == id
    )
    
    total = query.count()
    offset = (page - 1) * size
    items = query.order_by(TimelineActivity.created_at.desc()).offset(offset).limit(size).all()
    
    import math
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
        "pages": math.ceil(total / size) if size > 0 else 0
    }
"""

users_start = content.find('# Users')
if users_start != -1:
    new_content = content[:users_start] + activity_endpoints + "\n\n" + content[users_start:]
    with open('app/api/crm.py', 'w') as f:
        f.write(new_content)
    print("Activity Timeline endpoints injected successfully.")
else:
    print("Could not find '# Users' block to inject code.")
