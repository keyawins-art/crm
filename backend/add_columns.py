from sqlalchemy import create_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv(".env")
database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/crm_db")

engine = create_engine(database_url)

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE leads ADD COLUMN ai_score NUMERIC(5, 2);"))
        print("Added ai_score column")
    except Exception as e:
        print("Could not add ai_score:", e)
        
    try:
        conn.execute(text("ALTER TABLE leads ADD COLUMN ai_priority_explanation TEXT;"))
        print("Added ai_priority_explanation column")
    except Exception as e:
        print("Could not add ai_priority_explanation:", e)
