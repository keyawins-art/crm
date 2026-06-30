from app.db.database import SessionLocal
from app.models.role import Role, Permission, RolePermission
from sqlalchemy.orm import Session

def seed():
    db = SessionLocal()
    try:
        # Create System Administrator Role
        admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
        if not admin_role:
            admin_role = Role(name="System Administrator", description="Full access")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            
        sales_role = db.query(Role).filter(Role.name == "Sales Executive").first()
        if not sales_role:
            sales_role = Role(name="Sales Executive", description="Sales user access")
            db.add(sales_role)
            db.commit()
            db.refresh(sales_role)
            
        permissions = ["accounts:read", "accounts:create", "accounts:update", "accounts:delete",
                       "contacts:read", "contacts:create", "contacts:update", "contacts:delete",
                       "leads:read", "leads:create", "leads:update", "leads:delete",
                       "opportunities:read", "opportunities:create", "opportunities:update", "opportunities:delete"]
        
        for p in permissions:
            perm = db.query(Permission).filter(Permission.action == p).first()
            if not perm:
                perm = Permission(name=p, action=p, resource=p.split(':')[0], description=p)
                db.add(perm)
                db.commit()
                db.refresh(perm)
            
            # Add to admin
            if not db.query(RolePermission).filter_by(role_id=admin_role.id, permission_id=perm.id).first():
                db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
            
            # Add to sales (exclude delete)
            if "delete" not in p:
                if not db.query(RolePermission).filter_by(role_id=sales_role.id, permission_id=perm.id).first():
                    db.add(RolePermission(role_id=sales_role.id, permission_id=perm.id))

        db.commit()
        print("Database seeded with Admin and Sales Executive roles successfully.")
    except Exception as e:
        print("Seeding failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
