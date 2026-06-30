with open('app/schemas/crm.py', 'r') as f:
    schemas_content = f.read()

audit_schema = """
class AuditLogRead(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    entity_type: str
    entity_id: Optional[UUID] = None
    action: str
    details: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
"""
if "class AuditLogRead" not in schemas_content:
    schemas_content = schemas_content + "\n" + audit_schema
    with open('app/schemas/crm.py', 'w') as f:
        f.write(schemas_content)
    print("Injected AuditLogRead schema.")

with open('app/api/crm.py', 'r') as f:
    api_content = f.read()

if "AuditLogRead" not in api_content:
    api_content = api_content.replace("FunnelChart,", "FunnelChart, AuditLogRead,")
    
audit_code = """
@router.get("/audit-logs", response_model=List[AuditLogRead])
def get_audit_logs(
    current_user: User = Depends(require_permission("accounts:read")), # Must have basic CRM access
    db: Session = Depends(get_db),
):
    # Only show logs related to the user if they are a sales executive, otherwise all
    query = db.query(AuditLog)
    if current_user.role and current_user.role.name == "Sales Executive":
        query = query.filter(AuditLog.user_id == current_user.id)
        
    logs = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return logs
"""

users_idx = -1
lines = api_content.split('\n')
for i, line in enumerate(lines):
    if line.strip() == '# Users':
        users_idx = i
        break

if users_idx != -1:
    lines.insert(users_idx, audit_code)
    
    # Let's also patch convert_lead to add the audit log
    for i, line in enumerate(lines):
        if "lead.converted_opportunity_id = opportunity_id" in line:
            indent = line[:len(line) - len(line.lstrip())]
            lines.insert(i + 1, indent + "audit_log = AuditLog(")
            lines.insert(i + 2, indent + "    user_id=current_user.id,")
            lines.insert(i + 3, indent + "    action=AuditAction.UPDATED,")
            lines.insert(i + 4, indent + "    entity_type='Lead',")
            lines.insert(i + 5, indent + "    entity_id=lead.id,")
            lines.insert(i + 6, indent + "    details=f\"{current_user.first_name or 'User'} converted Lead\"")
            lines.insert(i + 7, indent + ")")
            lines.insert(i + 8, indent + "db.add(audit_log)")
            break

    new_api = '\n'.join(lines)
    with open('app/api/crm.py', 'w') as f:
        f.write(new_api)
    print("Injected Audit Log endpoint and convert_lead log.")
else:
    print("Could not find '# Users' to inject Audit Logs API endpoint.")
