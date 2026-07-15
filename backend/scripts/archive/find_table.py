import sys, os
from sqlalchemy import text
from app.db.database import SessionLocal

db = SessionLocal()
try:
    tables_res = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
    tables = [row[0] for row in tables_res.fetchall()]
    
    for table in tables:
        try:
            # We assume most tables have a 'name' or 'first_name' column we can check loosely by just casting the whole row to text
            res = db.execute(text(f"SELECT * FROM {table} WHERE CAST({table} AS text) ILIKE '%AdminAccount%' LIMIT 1"))
            if res.rowcount > 0:
                print(f"Found in table: {table}")
        except Exception as e:
            pass
finally:
    db.close()
