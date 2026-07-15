from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import Role, Permission

db = SessionLocal()

# Ensure products permissions exist
product_perms = [
    "products:read",
    "products:create",
    "products:update",
    "products:delete"
]

for p_name in product_perms:
    perm = db.query(Permission).filter(Permission.name == p_name).first()
    if not perm:
        action = p_name.split(":")[1]
        perm = Permission(name=p_name, resource="products", action=action)
        db.add(perm)
db.commit()

# Assign to System Administrator
admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
if admin_role:
    for p_name in product_perms:
        perm = db.query(Permission).filter(Permission.name == p_name).first()
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)

db.commit()
print("Added product permissions to System Administrator.")
