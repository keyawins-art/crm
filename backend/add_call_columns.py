from sqlalchemy import create_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv(".env")
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/crm_db")

engine = create_engine(database_url)

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE calls ADD COLUMN transcript TEXT;"))
        print("Added transcript column")
    except Exception as e:
        print("Could not add transcript:", e)
        
    try:
        conn.execute(text("ALTER TABLE calls ADD COLUMN notes TEXT;"))
        print("Added notes column")
    except Exception as e:
        print("Could not add notes:", e)
