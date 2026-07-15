from app.db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("DELETE FROM leads WHERE first_name LIKE '%Admin%' OR last_name LIKE '%Admin%' OR first_name LIKE '%Exec%' OR last_name LIKE '%Exec%' OR first_name LIKE '%Convert%' OR last_name LIKE '%Convert%' OR first_name LIKE '%Test%' OR last_name LIKE '%Test%'"))
    db.commit()
    print("Deleted all remaining test leads")
finally:
    db.close()
