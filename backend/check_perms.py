from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models import User, Role, Permission

db = SessionLocal()
user = db.query(User).filter(User.email == 'admin@example.com').first() # Or whatever email
if not user:
    user = db.query(User).first()
print(f"User: {user.email}")
print(f"Role: {user.role.name}")
for p in user.role.permissions:
    if 'products' in p.name:
        print(f"Permission: {p.name}")
