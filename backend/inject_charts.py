with open('app/schemas/crm.py', 'r') as f:
    schemas_content = f.read()

charts_schemas = """
class MonthlyLeadChart(BaseModel):
    month: str
    count: int

class RevenueChart(BaseModel):
    month: str
    revenue: float

class FunnelChart(BaseModel):
    stage: str
    count: int
"""
if "class MonthlyLeadChart" not in schemas_content:
    schemas_content = schemas_content + "\n" + charts_schemas
    with open('app/schemas/crm.py', 'w') as f:
        f.write(schemas_content)
    print("Injected Charts schemas.")

with open('app/api/crm.py', 'r') as f:
    api_content = f.read()

if "MonthlyLeadChart" not in api_content:
    api_content = api_content.replace("KPIRead,", "KPIRead, MonthlyLeadChart, RevenueChart, FunnelChart,")
    
charts_code = """
@router.get("/reports/monthly-leads", response_model=List[MonthlyLeadChart])
def get_monthly_leads(
    current_user: User = Depends(require_permission("leads:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    query = db.query(Lead).filter(Lead.is_deleted == False)
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            query = query.filter(Lead.owner_id == current_user.id)
            
    # Group by YYYY-MM
    results = (
        db.query(
            func.to_char(Lead.created_at, 'YYYY-MM').label("month"),
            func.count(Lead.id).label("count")
        )
        .filter(Lead.is_deleted == False)
    )
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Lead, 'owner_id'):
            results = results.filter(Lead.owner_id == current_user.id)
            
    results = results.group_by("month").order_by("month").all()
    
    return [{"month": r.month, "count": r.count} for r in results]


@router.get("/reports/revenue", response_model=List[RevenueChart])
def get_revenue_report(
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    # Group by YYYY-MM of close_date
    results = (
        db.query(
            func.to_char(Opportunity.close_date, 'YYYY-MM').label("month"),
            func.sum(Opportunity.amount).label("revenue")
        )
        .filter(Opportunity.is_deleted == False)
    )
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'assigned_to_id'):
            results = results.filter(Opportunity.assigned_to_id == current_user.id)
            
    results = results.group_by("month").order_by("month").all()
    
    return [{"month": r.month, "revenue": float(r.revenue or 0)} for r in results]


@router.get("/reports/funnel", response_model=List[FunnelChart])
def get_funnel_report(
    current_user: User = Depends(require_permission("opportunities:read")),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func
    
    results = (
        db.query(
            Opportunity.stage,
            func.count(Opportunity.id).label("count")
        )
        .filter(Opportunity.is_deleted == False)
    )
    
    if current_user.role and current_user.role.name == "Sales Executive":
        if hasattr(Opportunity, 'assigned_to_id'):
            results = results.filter(Opportunity.assigned_to_id == current_user.id)
            
    results = results.group_by(Opportunity.stage).all()
    
    return [{"stage": r.stage.value if hasattr(r.stage, 'value') else str(r.stage), "count": r.count} for r in results]

"""

users_idx = -1
lines = api_content.split('\n')
for i, line in enumerate(lines):
    if line.strip() == '# Users':
        users_idx = i
        break

if users_idx != -1:
    lines.insert(users_idx, charts_code)
    new_api = '\n'.join(lines)
    with open('app/api/crm.py', 'w') as f:
        f.write(new_api)
    print("Injected Charts API endpoints.")
else:
    print("Could not find '# Users' to inject Charts API endpoints.")
