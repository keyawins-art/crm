from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("SELECT id, first_name, last_name, company FROM leads ORDER BY created_at DESC LIMIT 10"))
    for row in res.fetchall():
        print(row)
finally:
    db.close()
