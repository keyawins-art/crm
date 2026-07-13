import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.db.database import engine

with engine.begin() as con:
    res = con.execute(text("DELETE FROM accounts WHERE name = 'OpenAI Pvt Ltd'"))
    print(f'Deleted {res.rowcount} accounts')
