from sqlalchemy import text
from app.db.database import engine
from app.db.database import create_all_tables

print("Creating new tables...")
create_all_tables()

print("Altering existing tables if needed...")
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE quotations ADD COLUMN IF NOT EXISTS billing_address TEXT;"))
        conn.execute(text("ALTER TABLE quotations ADD COLUMN IF NOT EXISTS shipping_address TEXT;"))
        conn.commit()
        print("Migration successful: added billing_address and shipping_address to quotations.")
    except Exception as e:
        print("Migration error:", e)
