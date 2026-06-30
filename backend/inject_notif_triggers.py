with open('app/api/crm.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = 0

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # 1. create_lead Notification
    if "def create_lead(" in line:
        # We need to insert after db.refresh(obj) in create_lead
        pass
    
    if "db.refresh(obj)" in line:
        # We need to be careful, this is generic.
        # Let's check context.
        # It's better to just write a simple logic that replaces the whole file by inserting the specific triggers.
        pass

# It's safer to use string replacement since we know the exact lines
with open('app/api/crm.py', 'r') as f:
    content = f.read()

# create_lead assignment
create_lead_find = """    db.refresh(obj)
    return obj"""

create_lead_replace = """    db.refresh(obj)
    
    if hasattr(obj, 'assigned_to_id') and obj.assigned_to_id and obj.assigned_to_id != current_user.id:
        send_notification(
            db=db,
            user_id=obj.assigned_to_id,
            title="Lead Assigned",
            message=f"You have been assigned a new lead: {obj.first_name} {obj.last_name}",
            type=NotificationType.INFO
        )
        
    return obj"""

# But `db.refresh(obj)\n    return obj` is used in MANY places (Account, Contact, etc).
# We should only replace the one in create_lead and update_lead.
