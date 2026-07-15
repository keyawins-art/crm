import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.db.database import engine

with engine.begin() as con:
    res = con.execute(text("SELECT id FROM roles WHERE name = 'Sales Executive'")).fetchone()
    if res:
        role_id = res[0]
        perm_res = con.execute(text("SELECT id FROM permissions WHERE name = 'users:read'")).fetchone()
        if perm_res:
            perm_id = perm_res[0]
            check = con.execute(text("SELECT 1 FROM role_permissions WHERE role_id = :r AND permission_id = :p"), {'r': role_id, 'p': perm_id}).fetchone()
            if not check:
                con.execute(text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:r, :p)"), {'r': role_id, 'p': perm_id})
                print('Permission assigned')
            else:
                print('Already assigned')
        else:
            print('Permission not found')
    else:
        print('Role not found')
