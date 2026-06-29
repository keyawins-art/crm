import re

with open('app/api/crm.py', 'r') as f:
    content = f.read()

# Add AuditLog imports if missing
if "from app.models.audit import AuditLog, AuditAction" not in content:
    content = content.replace("from app.models import (", "from app.models.audit import AuditLog, AuditAction\nfrom app.models import (")

# Add log_audit function
log_audit_func = """
def log_audit(db: Session, user: User, action: AuditAction, entity_type: str, entity_id: UUID):
    user_name = user.first_name or "User"
    action_str = "created" if action == AuditAction.CREATED else "updated" if action == AuditAction.UPDATED else "deleted"
    message = f"{user_name} {action_str} {entity_type}"
    
    audit_log = AuditLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=message
    )
    db.add(audit_log)
    # We do NOT commit here, we rely on the caller's transaction
"""

if "def log_audit" not in content:
    idx = content.find('@router.get("/health"')
    content = content[:idx] + log_audit_func + "\n\n" + content[idx:]


# We will inject the log_audit call right before db.commit() in create, update, delete, hard_delete, restore.

# Create
content = re.sub(
    r'(db\.add\(obj\)\n\s+db\.commit\(\))',
    r'\1\n    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)\n    db.commit() # secondary commit for audit if needed, but actually we should log before commit.',
    content
)

# Fix the above regex since we want to insert it before commit. Let's do it cleanly:
content = re.sub(
    r'(db\.add\(obj\)\n\s+)(db\.commit\(\))',
    r'\1db.flush()\n    log_audit(db, current_user, AuditAction.CREATED, obj.__class__.__name__, obj.id)\n    \2',
    content
)

# Update
content = re.sub(
    r'(setattr\(obj, key, value\)\n\s+)(db\.commit\(\))',
    r'\1log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)\n    \2',
    content
)

# Delete (Soft)
content = re.sub(
    r'(obj\.deleted_at = func\.now\(\)\n\s+)(db\.commit\(\))',
    r'\1log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)\n    \2',
    content
)

# Delete (Hard)
content = re.sub(
    r'(db\.delete\(obj\)\n\s+)(db\.commit\(\))',
    r'\1log_audit(db, current_user, AuditAction.DELETED, obj.__class__.__name__, obj.id)\n    \2',
    content
)

# Restore
content = re.sub(
    r'(obj\.deleted_at = None\n\s+)(db\.commit\(\))',
    r'\1log_audit(db, current_user, AuditAction.UPDATED, obj.__class__.__name__, obj.id)\n    \2',
    content
)


# Add the GET /audit-logs endpoint to app/api/dashboard.py instead of crm.py to keep things clean.
# Wait, I'll just write it to dashboard.py in a separate step.

with open('app/api/crm.py', 'w') as f:
    f.write(content)
print("Audit logging injected successfully.")
