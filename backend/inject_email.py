with open('app/api/crm.py', 'r') as f:
    content = f.read()

# 1. Imports
if "BackgroundTasks" not in content:
    content = content.replace("from fastapi import APIRouter, Request, Depends, HTTPException, Query, status", "from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, BackgroundTasks")

if "from app.core.email import send_email" not in content:
    content = content.replace("from app.core.rbac import require_permission", "from app.core.rbac import require_permission\nfrom app.core.email import send_email")

# 2. Modify create_lead
create_lead_sig = """def create_lead(
    payload: LeadCreate,
    current_user: User = Depends(require_permission("leads:create")),
    db: Session = Depends(get_db),
):"""
new_create_lead_sig = """def create_lead(
    payload: LeadCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("leads:create")),
    db: Session = Depends(get_db),
):"""
content = content.replace(create_lead_sig, new_create_lead_sig)

create_lead_return = """    db.refresh(obj)
    return obj"""
new_create_lead_return = """    db.refresh(obj)
    if obj.email:
        background_tasks.add_task(
            send_email,
            obj.email,
            "Welcome to our CRM!",
            f"Hi {obj.first_name},\\n\\nThank you for connecting with us. We will follow up shortly.\\n\\nBest regards,\\nSales Team"
        )
    return obj"""
# We only want to replace the first occurrence after the signature.
if new_create_lead_return not in content:
    content = content.replace(create_lead_return, new_create_lead_return, 1)

# 3. Modify add_lead_activity
add_activity_sig = """def add_lead_activity(
    id: UUID,
    payload: LeadActivityCreate,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):"""
new_add_activity_sig = """def add_lead_activity(
    id: UUID,
    payload: LeadActivityCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("leads:update")),
    db: Session = Depends(get_db),
):"""
content = content.replace(add_activity_sig, new_add_activity_sig)

add_activity_return = """    db.refresh(activity)
    return activity"""
new_add_activity_return = """    db.refresh(activity)
    if activity.type == 'email' and lead.email:
        background_tasks.add_task(
            send_email,
            lead.email,
            activity.subject or "Follow-up",
            activity.description or f"Hi {lead.first_name},\\n\\nThis is a follow up regarding our previous conversation.\\n\\nBest regards,\\nSales Team"
        )
    return activity"""
if new_add_activity_return not in content:
    content = content.replace(add_activity_return, new_add_activity_return, 1)

# 4. Modify update_quotation
update_quotation_sig = """def update_quotation(
    id: UUID,
    payload: QuotationUpdate,
    current_user: User = Depends(require_permission("quotations:update")),
    db: Session = Depends(get_db),
):"""
new_update_quotation_sig = """def update_quotation(
    id: UUID,
    payload: QuotationUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("quotations:update")),
    db: Session = Depends(get_db),
):"""
content = content.replace(update_quotation_sig, new_update_quotation_sig)

update_quotation_return = """    db.refresh(obj)
    return obj"""
new_update_quotation_return = """    db.refresh(obj)
    if 'status' in update_data and str(update_data['status']).lower() == 'sent' and obj.opportunity and obj.opportunity.contact and obj.opportunity.contact.email:
        background_tasks.add_task(
            send_email,
            obj.opportunity.contact.email,
            f"Quotation {getattr(obj, 'quote_number', 'unknown')} Attached",
            f"Hi {obj.opportunity.contact.first_name},\\n\\nPlease find the attached quotation for {obj.opportunity.name}.\\n\\nTotal Amount: {obj.total_amount}\\n\\nBest regards,\\nSales Team"
        )
    return obj"""
if new_update_quotation_return not in content:
    content = content.replace(update_quotation_return, new_update_quotation_return, 1)

with open('app/api/crm.py', 'w') as f:
    f.write(content)

print("Injected Email Logic!")
