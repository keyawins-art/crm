with open('app/api/crm.py', 'r') as f:
    content = f.read()

if "from app.models.activity import TimelineActivity" not in content:
    content = content.replace("from app.models.lead import LeadStatus", "from app.models.activity import TimelineActivity\nfrom app.models.lead import LeadStatus")

if "from app.schemas.activity import ActivityRead" not in content:
    content = "from app.schemas.activity import ActivityRead\n" + content

if "from typing import List" not in content:
    content = "from typing import List\n" + content

timeline_code = """
@router.get("/leads/{id}/timeline", response_model=List[ActivityRead])
def get_lead_timeline(
    id: UUID,
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    query = db.query(Lead).filter(Lead.id == id, Lead.is_deleted == False)
    
    # RLS Enforcement
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
        elif hasattr(Lead, 'assigned_to_id'):
            if hasattr(Lead, 'created_by_id'):
                from sqlalchemy import or_
                query = query.filter(or_(Lead.assigned_to_id == current_user.id, Lead.created_by_id == current_user.id))
            else:
                query = query.filter(Lead.assigned_to_id == current_user.id)
        elif hasattr(Lead, 'created_by_id'):
            query = query.filter(Lead.created_by_id == current_user.id)

    lead = query.first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    activities = db.query(TimelineActivity).filter(
        TimelineActivity.entity_type == "leads",
        TimelineActivity.entity_id == id
    ).order_by(TimelineActivity.created_at.desc()).all()
    
    return activities

"""

# Insert before # Users block
users_start = content.find('# Users')
if users_start != -1:
    new_content = content[:users_start] + timeline_code + content[users_start:]
    with open('app/api/crm.py', 'w') as f:
        f.write(new_content)
    print("Lead Timeline endpoint added successfully.")
else:
    print("Could not find '# Users' to inject code before.")
