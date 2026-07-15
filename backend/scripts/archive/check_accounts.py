from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("SELECT name FROM accounts ORDER BY created_at DESC LIMIT 10"))
    for row in res.fetchall():
        print(row)
finally:
    db.close()
