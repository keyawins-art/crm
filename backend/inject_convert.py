with open('app/api/crm.py', 'r') as f:
    content = f.read()

# Make sure we have necessary imports
if "LeadConvert" not in content:
    content = content.replace("LeadUpdate,", "LeadUpdate, LeadConvert, LeadConversionResponse,")

if "from datetime import date, timedelta" not in content:
    content = "from datetime import date, timedelta\n" + content

if "from app.models.lead import LeadStatus" not in content:
    content = content.replace("from app.models import (", "from app.models.lead import LeadStatus\nfrom app.models.opportunity import OpportunityStage\nfrom app.models import (")

convert_code = """
@router.post("/leads/{id}/convert", response_model=LeadConversionResponse)
def convert_lead(
    id: UUID,
    payload: LeadConvert,
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
        
    if lead.is_converted:
        raise HTTPException(status_code=400, detail="Lead is already converted")

    from sqlalchemy.sql import func
    
    # 1. Handle Account
    account_id = payload.account_id
    if not account_id:
        acc_name = lead.company if lead.company else (lead.first_name + " " + lead.last_name)
        account = Account(
            name=acc_name,
            industry=lead.industry,
            annual_revenue=lead.annual_revenue,
            owner_id=lead.assigned_to_id or current_user.id,
            created_by_id=current_user.id
        )
        db.add(account)
        db.flush()
        account_id = account.id

    # 2. Handle Contact
    contact_id = payload.contact_id
    if not contact_id:
        contact = Contact(
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            mobile=lead.mobile,
            title=lead.title,
            account_id=account_id,
            owner_id=lead.assigned_to_id or current_user.id,
            created_by_id=current_user.id
        )
        db.add(contact)
        db.flush()
        contact_id = contact.id

    # 3. Handle Opportunity
    opportunity_id = None
    if payload.create_opportunity:
        opp_name = payload.opportunity_name
        if not opp_name:
            acc_name = lead.company if lead.company else (lead.first_name + " " + lead.last_name)
            opp_name = f"{acc_name} - Deal"
            
        opportunity = Opportunity(
            name=opp_name,
            stage=OpportunityStage.PROSPECTING,
            amount=payload.amount,
            close_date=date.today() + timedelta(days=30),
            account_id=account_id,
            contact_id=contact_id,
            lead_id=lead.id,
            assigned_to_id=lead.assigned_to_id or current_user.id,
            created_by_id=current_user.id
        )
        db.add(opportunity)
        db.flush()
        opportunity_id = opportunity.id

    # 4. Update Lead
    lead.is_converted = True
    lead.status = LeadStatus.CONVERTED
    lead.converted_at = func.now()
    lead.converted_account_id = account_id
    lead.converted_contact_id = contact_id
    lead.converted_opportunity_id = opportunity_id
    
    db.commit()
    db.refresh(lead)
    
    return LeadConversionResponse(
        lead_id=lead.id,
        account_id=account_id,
        contact_id=contact_id,
        opportunity_id=opportunity_id,
        status="converted"
    )

"""

# Insert before # Users block
users_start = content.find('# Users')
if users_start != -1:
    new_content = content[:users_start] + convert_code + content[users_start:]
    with open('app/api/crm.py', 'w') as f:
        f.write(new_content)
    print("Lead Convert endpoint added successfully.")
else:
    print("Could not find '# Users' to inject code before.")
