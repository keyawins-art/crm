import os
import sys
# Add current path to sys.path so app module can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine
from sqlalchemy import text

def main():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(255);"))
            conn.commit()
            print("image_url added")
        except Exception as e:
            print("image_url err:", e)

        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN specifications JSONB;"))
            conn.commit()
            print("specifications added")
        except Exception as e:
            print("specifications err:", e)

if __name__ == "__main__":
    main()
