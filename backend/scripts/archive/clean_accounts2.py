from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("DELETE FROM accounts WHERE name ILIKE '%AdminAccount%' OR name ILIKE '%Blocked%' OR name ILIKE '%Conversion Inc%' OR name ILIKE '%Test Corp%'"))
    db.commit()
    print(f"Deleted {res.rowcount} test accounts")
finally:
    db.close()
