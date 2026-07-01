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
        conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255);"))
        conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS source VARCHAR(255);"))
        conn.execute(text("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS product_of_interest VARCHAR(255);"))
        conn.commit()
        print("Migration successful: added custom columns to quotations and accounts.")
    except Exception as e:
        print("Migration error:", e)
