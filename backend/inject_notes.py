with open('app/schemas/crm.py', 'r') as f:
    schemas_content = f.read()

notes_schemas = """
class LeadNoteCreate(BaseModel):
    content: str
    is_pinned: Optional[bool] = False

class LeadNoteRead(LeadNoteCreate):
    id: UUID
    lead_id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
"""
if "class LeadNoteCreate" not in schemas_content:
    schemas_content = schemas_content + "\n" + notes_schemas
    with open('app/schemas/crm.py', 'w') as f:
        f.write(schemas_content)
    print("Injected Notes schemas.")

with open('app/api/crm.py', 'r') as f:
    api_content = f.read()

if "from app.models.lead import LeadNote" not in api_content:
    api_content = api_content.replace("from app.models.lead import LeadStatus", "from app.models.lead import LeadStatus, LeadNote")
if "from app.schemas.crm import" in api_content and "LeadNoteCreate" not in api_content:
    api_content = api_content.replace("LeadConvert,", "LeadConvert, LeadNoteCreate, LeadNoteRead,")
    
notes_code = """
@router.post("/leads/{id}/notes", response_model=LeadNoteRead)
def add_lead_note(
    id: UUID,
    payload: LeadNoteCreate,
    current_user: User = Depends(require_permission("leads:update")),
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
        
    note = LeadNote(
        lead_id=id,
        user_id=current_user.id,
        content=payload.content,
        is_pinned=payload.is_pinned
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.get("/leads/{id}/notes", response_model=List[LeadNoteRead])
def get_lead_notes(
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
        
    notes = db.query(LeadNote).filter(LeadNote.lead_id == id).order_by(LeadNote.created_at.desc()).all()
    return notes

"""

users_start = api_content.find('# Users')
if users_start != -1:
    new_api = api_content[:users_start] + notes_code + api_content[users_start:]
    with open('app/api/crm.py', 'w') as f:
        f.write(new_api)
    print("Injected Notes endpoint.")
else:
    print("Could not find '# Users' to inject notes endpoint.")
