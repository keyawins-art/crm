import re

with open('app/api/crm.py', 'r') as f:
    content = f.read()

if "from app.api.notifications import send_notification" not in content:
    content = "from app.api.notifications import send_notification\nfrom app.models.audit import NotificationType\n" + content

# 1. Lead Assigned Trigger (Create)
lead_create_pattern = r'(@router\.post\("/leads".*?def create_lead\([^)]+\):.*?)(db\.commit\(\))'
def inject_lead_create_notif(match):
    return match.group(1) + """
    if obj.assigned_to_id and obj.assigned_to_id != current_user.id:
        send_notification(
            db=db,
            user_id=obj.assigned_to_id,
            title="New Lead Assigned",
            message=f"A new lead '{obj.first_name} {obj.last_name}' has been assigned to you.",
            type=NotificationType.INFO
        )
    """ + match.group(2)

content = re.sub(lead_create_pattern, inject_lead_create_notif, content, flags=re.DOTALL)

# 2. Lead Assigned Trigger (Update)
lead_update_pattern = r'(@router\.put\("/leads/\{id\}".*?def update_lead\([^)]+\):.*?)(db\.commit\(\))'
def inject_lead_update_notif(match):
    return match.group(1) + """
    # Check if assigned_to_id was in payload
    if getattr(payload, 'assigned_to_id', None) and payload.assigned_to_id != current_user.id:
        send_notification(
            db=db,
            user_id=payload.assigned_to_id,
            title="Lead Re-assigned",
            message=f"Lead '{obj.first_name} {obj.last_name}' has been assigned to you.",
            type=NotificationType.INFO
        )
    """ + match.group(2)

content = re.sub(lead_update_pattern, inject_lead_update_notif, content, flags=re.DOTALL)

# 3. Quotation Approved Trigger (Update)
quotation_update_pattern = r'(@router\.put\("/quotations/\{id\}".*?def update_quotation\([^)]+\):.*?)(db\.commit\(\))'
def inject_quotation_update_notif(match):
    return match.group(1) + """
    # Check if status was updated to APPROVED
    if getattr(payload, 'status', None) and payload.status == "APPROVED":
        send_notification(
            db=db,
            user_id=obj.created_by_id or obj.assigned_to_id,
            title="Quotation Approved",
            message=f"Your quotation '{obj.name}' has been approved!",
            type=NotificationType.SUCCESS
        )
    """ + match.group(2)

content = re.sub(quotation_update_pattern, inject_quotation_update_notif, content, flags=re.DOTALL)

with open('app/api/crm.py', 'w') as f:
    f.write(content)

print("Notification triggers injected successfully.")
