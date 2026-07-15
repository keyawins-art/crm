import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.db.database import engine

with engine.begin() as con:
    # Check if tasktype enum exists
    res = con.execute(text("SELECT 1 FROM pg_type WHERE typname = 'tasktype'")).fetchone()
    if not res:
        con.execute(text("CREATE TYPE tasktype AS ENUM ('email', 'task', 'meeting', 'follow_up', 'call')"))
        print("Created tasktype ENUM")
    
    # Check if task_type column exists
    res = con.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='task_type'")).fetchone()
    if not res:
        con.execute(text("ALTER TABLE tasks ADD COLUMN task_type tasktype DEFAULT 'task'"))
        print("Added task_type column")
        
    # Check if account_id column exists
    res = con.execute(text("SELECT 1 FROM information_schema.columns WHERE table_name='tasks' AND column_name='account_id'")).fetchone()
    if not res:
        con.execute(text("ALTER TABLE tasks ADD COLUMN account_id UUID REFERENCES accounts(id) ON DELETE SET NULL"))
        print("Added account_id column")

print("Tasks table schema updated successfully.")
