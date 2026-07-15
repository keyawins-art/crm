from app.db.database import SessionLocal
from app.models.contact import Contact

db = SessionLocal()
try:
    res = db.query(Contact).all()
    for c in res:
        print(f"{c.first_name} {c.last_name} (Company: {c.company_name})")
finally:
    db.close()
