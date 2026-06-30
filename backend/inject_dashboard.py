with open('app/schemas/crm.py', 'r') as f:
    schemas_content = f.read()

dashboard_schema = """
class DashboardRead(BaseModel):
    accounts: int
    contacts: int
    leads: int
    opportunities: int
    revenue: float
"""
if "class DashboardRead" not in schemas_content:
    schemas_content = schemas_content + "\n" + dashboard_schema
    with open('app/schemas/crm.py', 'w') as f:
        f.write(schemas_content)
    print("Injected Dashboard schema.")

with open('app/api/crm.py', 'r') as f:
    api_content = f.read()

if "DashboardRead" not in api_content:
    api_content = api_content.replace("LeadActivityRead,", "LeadActivityRead, DashboardRead,")
    
dashboard_code = """
@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(
    current_user: User = Depends(require_permission("accounts:read")), # Base permission check
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    # 1. Accounts Count
    acc_query = db.query(Account).filter(Account.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Account, 'owner_id'):
            acc_query = acc_query.filter(Account.owner_id == current_user.id)
    accounts_count = acc_query.count()

    # 2. Contacts Count
    cont_query = db.query(Contact).filter(Contact.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Contact, 'owner_id'):
            cont_query = cont_query.filter(Contact.owner_id == current_user.id)
    contacts_count = cont_query.count()

    # 3. Leads Count
    lead_query = db.query(Lead).filter(Lead.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            lead_query = lead_query.filter(Lead.owner_id == current_user.id)
    leads_count = lead_query.count()

    # 4. Opportunities Count & Revenue
    opp_query = db.query(Opportunity).filter(Opportunity.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'assigned_to_id'):
            opp_query = opp_query.filter(Opportunity.assigned_to_id == current_user.id)
    
    opportunities_count = opp_query.count()
    revenue = db.query(func.sum(Opportunity.amount)).filter(Opportunity.is_deleted == False).scalar() or 0.0

    return {
        "accounts": accounts_count,
        "contacts": contacts_count,
        "leads": leads_count,
        "opportunities": opportunities_count,
        "revenue": float(revenue)
    }

"""

# Insert before the dynamic routes block
dynamic_route_idx = -1
lines = api_content.split('\n')
for i, line in enumerate(lines):
    if '@router.post("/{module_name}' in line:
        dynamic_route_idx = i
        break

if dynamic_route_idx != -1:
    lines.insert(dynamic_route_idx, dashboard_code)
    new_api = '\n'.join(lines)
    with open('app/api/crm.py', 'w') as f:
        f.write(new_api)
    print("Injected Dashboard endpoint.")
else:
    print("Could not find dynamic route marker to inject dashboard endpoint.")
