from app.db.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
res = db.execute(text("SELECT enum_range(NULL::salesorderstatus)")).scalar()
print('SalesOrderStatus:', res)
