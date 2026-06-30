from app.db.database import SessionLocal
from app.models.role import Role, Permission, RolePermission
from app.models.user import User
from app.core.security import get_password_hash
import urllib.request
import urllib.parse
import urllib.error
import json

base_url = "http://127.0.0.1:8000"

# Setup DB
db = SessionLocal()
try:
    # Promote vikas@example.com to System Administrator
    admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
    vikas = db.query(User).filter(User.email == "vikas@example.com").first()
    if vikas and admin_role:
        vikas.role_id = admin_role.id
        db.commit()

    # Create Support role
    support_role = db.query(Role).filter(Role.name == "Support").first()
    if not support_role:
        support_role = Role(name="Support", description="Support team")
        db.add(support_role)
        db.commit()
        db.refresh(support_role)
        
        # Give only accounts:read permission
        perm = db.query(Permission).filter(Permission.action == "accounts:read").first()
        if perm:
            db.add(RolePermission(role_id=support_role.id, permission_id=perm.id))
            db.commit()
            
    # Setup support user directly
    support_user = db.query(User).filter(User.email == "support@crm.com").first()
    if not support_user:
        support_user = User(
            email="support@crm.com",
            first_name="Support",
            last_name="User",
            password_hash=get_password_hash("support"),
            role_id=support_role.id
        )
        db.add(support_user)
    else:
        support_user.password_hash = get_password_hash("support")
        support_user.role_id = support_role.id
    db.commit()
finally:
    db.close()

def login(username, password):
    data = urllib.parse.urlencode({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/auth/login", data=data)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))["access_token"]
    except Exception as e:
        print(f"Login failed for {username}: {e}")
        return None

def make_request(method, endpoint, token, payload=None):
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if payload:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        
    req = urllib.request.Request(f"{base_url}{endpoint}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

print("\n--- Testing Admin User (vikas@example.com) ---")
admin_token = login("vikas@example.com", "vikas")
if admin_token:
    status, resp = make_request("POST", "/crm/accounts", admin_token, {"name": "Admin Test Account"})
    print(f"POST /crm/accounts -> {status} (Expected: 201 or 200)")

print("\n--- Testing Support User (support@crm.com) ---")
support_token = login("support@crm.com", "support")
if support_token:
    status, resp = make_request("POST", "/crm/accounts", support_token, {"name": "Support Test Account"})
    print(f"POST /crm/accounts -> {status} (Expected: 403)")

    status, resp = make_request("GET", "/crm/accounts?size=1", support_token)
    print(f"GET /crm/accounts -> {status} (Expected: 200)")
