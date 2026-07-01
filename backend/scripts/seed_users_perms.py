import uuid
import datetime
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:anything@127.0.0.1:5432/crm_db')
with engine.begin() as con:
    res = con.execute(text("SELECT id FROM roles WHERE name = 'System Administrator'")).fetchone()
    if not res:
        print('Role not found')
        exit()
    role_id = res[0]
    
    perms = [
        ('users:read', 'users', 'read'), 
        ('users:create', 'users', 'create'), 
        ('users:update', 'users', 'update'), 
        ('users:delete', 'users', 'delete')
    ]
    
    for name, resource, action in perms:
        res = con.execute(text("SELECT id FROM permissions WHERE name = :name"), {'name': name}).fetchone()
        if res:
            perm_id = res[0]
        else:
            perm_id = uuid.uuid4()
            now = datetime.datetime.now(datetime.timezone.utc)
            con.execute(
                text("INSERT INTO permissions (id, name, resource, action, description, created_at, updated_at) VALUES (:id, :name, :resource, :action, :desc, :created_at, :updated_at)"),
                {'id': perm_id, 'name': name, 'resource': resource, 'action': action, 'desc': f'Can {action} {resource}', 'created_at': now, 'updated_at': now}
            )
            print(f'Inserted permission {name}')
            
        res = con.execute(
            text("SELECT 1 FROM role_permissions WHERE role_id = :r AND permission_id = :p"),
            {'r': role_id, 'p': perm_id}
        ).fetchone()
        
        if not res:
            con.execute(
                text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:r, :p)"),
                {'r': role_id, 'p': perm_id}
            )
            print(f'Mapped {name} to System Administrator')
