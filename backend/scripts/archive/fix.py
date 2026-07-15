from app.db.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
db.execute(text("UPDATE alembic_version SET version_num = 'dbb55e7e51ec'"))
db.commit()
