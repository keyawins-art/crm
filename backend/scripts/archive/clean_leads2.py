from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    res = db.execute(text("DELETE FROM leads WHERE first_name IN ('Jane', 'John', 'SUNNY') OR last_name IN ('Smith', 'Doe', 'BERVA')"))
    db.commit()
    print(f"Deleted {res.rowcount} more test leads")
finally:
    db.close()
