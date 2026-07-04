#!/usr/bin/env python3
"""Create or reset an admin user for CRM."""
import sys
sys.path.insert(0, '.')

from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.models.user import User
from app.models.role import Role

db = SessionLocal()

admin_role = db.query(Role).filter(Role.name == "admin").first()
if not admin_role:
    admin_role = db.query(Role).first()

admin = db.query(User).filter(User.email == "admin@crm.com").first()
if admin:
    admin.password_hash = get_password_hash("admin123")
    print("Reset password for admin@crm.com")
else:
    admin = User(
        email="admin@crm.com",
        first_name="Admin",
        last_name="CRM",
        password_hash=get_password_hash("admin123"),
        is_active=True,
        role_id=admin_role.id if admin_role else None,
    )
    db.add(admin)
    print("Created admin@crm.com with password admin123")

db.commit()
db.close()
print("Done! Login with: admin@crm.com / admin123")
