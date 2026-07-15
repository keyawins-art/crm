from app.db.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
res = db.execute(text("SELECT enum_range(NULL::quotationstatus)")).scalar()
print('QuotationStatus:', res)
res2 = db.execute(text("SELECT enum_range(NULL::opportunitystage)")).scalar()
print('OpportunityStage:', res2)
