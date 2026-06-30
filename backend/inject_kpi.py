with open('app/schemas/crm.py', 'r') as f:
    schemas_content = f.read()

kpi_schema = """
class KPIRead(BaseModel):
    conversion_rate: float
    win_rate: float
    lost_rate: float
"""
if "class KPIRead" not in schemas_content:
    schemas_content = schemas_content + "\n" + kpi_schema
    with open('app/schemas/crm.py', 'w') as f:
        f.write(schemas_content)
    print("Injected KPI schema.")

with open('app/api/crm.py', 'r') as f:
    api_content = f.read()

if "KPIRead" not in api_content:
    api_content = api_content.replace("DashboardRead,", "DashboardRead, KPIRead,")
    
kpi_code = """
@router.get("/dashboard/kpi", response_model=KPIRead)
def get_dashboard_kpi(
    current_user: User = Depends(require_permission("accounts:read")),
    db: Session = Depends(get_db),
):
    # Base queries with RLS
    lead_query = db.query(Lead).filter(Lead.is_deleted == False)
    opp_query = db.query(Opportunity).filter(Opportunity.is_deleted == False)
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            lead_query = lead_query.filter(Lead.owner_id == current_user.id)
        if hasattr(Opportunity, 'assigned_to_id'):
            opp_query = opp_query.filter(Opportunity.assigned_to_id == current_user.id)
            
    # Lead Conversion Rate
    total_leads = lead_query.count()
    converted_leads = lead_query.filter(Lead.status == LeadStatus.CONVERTED).count()
    conversion_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0.0

    # Win / Loss Rate
    total_opps = opp_query.count()
    won_opps = opp_query.filter(Opportunity.stage == OpportunityStage.CLOSED_WON).count()
    lost_opps = opp_query.filter(Opportunity.stage == OpportunityStage.CLOSED_LOST).count()
    
    win_rate = round((won_opps / total_opps * 100), 2) if total_opps > 0 else 0.0
    lost_rate = round((lost_opps / total_opps * 100), 2) if total_opps > 0 else 0.0

    return {
        "conversion_rate": conversion_rate,
        "win_rate": win_rate,
        "lost_rate": lost_rate
    }

"""

# Insert just before # Users block
users_idx = -1
lines = api_content.split('\n')
for i, line in enumerate(lines):
    if line.strip() == '# Users':
        users_idx = i
        break

if users_idx != -1:
    lines.insert(users_idx, kpi_code)
    new_api = '\n'.join(lines)
    with open('app/api/crm.py', 'w') as f:
        f.write(new_api)
    print("Injected KPI endpoint.")
else:
    print("Could not find '# Users' to inject KPI endpoint.")
