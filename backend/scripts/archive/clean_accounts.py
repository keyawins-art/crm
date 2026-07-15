from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("DELETE FROM accounts WHERE name LIKE '%AdminAccount%' OR name = 'Blocked' OR name = 'Conversion Inc' OR name = 'Test Corp'"))
    db.commit()
    print(f"Deleted {res.rowcount} test accounts")
finally:
    db.close()
