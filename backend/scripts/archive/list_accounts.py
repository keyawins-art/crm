from app.db.database import SessionLocal
from app.models.account import Account

db = SessionLocal()
try:
    res = db.query(Account).all()
    for a in res:
        print(a.name)
finally:
    db.close()
