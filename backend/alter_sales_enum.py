from app.db.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    db.execute(text("ALTER TYPE salesorderstatus ADD VALUE 'PROCESSING'"))
    db.execute(text("ALTER TYPE salesorderstatus ADD VALUE 'SHIPPED'"))
    db.execute(text("ALTER TYPE salesorderstatus ADD VALUE 'DELIVERED'"))
    db.commit()
    print("Successfully added new enum values.")
except Exception as e:
    print("Failed:", e)
    db.rollback()
