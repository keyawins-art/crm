from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
try:
    u = db.query(User).filter(User.email == 'admin@crm.com').first()
    if u:
        u.password_hash = get_password_hash('admin123')
        db.commit()
        print("Password reset to admin123")
    else:
        print("Admin user not found")
finally:
    db.close()
