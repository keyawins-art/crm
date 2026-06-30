import urllib.request
import urllib.parse
import urllib.error
import json
import time

# Use DB session to fetch a valid user ID and clean up workflows
from app.db.database import SessionLocal
from app.models.user import User
from app.models.workflow import WorkflowRule

db = SessionLocal()
try:
    # 0. Clean up existing workflows directly in DB
    print("\n--- 0. Cleaning up existing workflows ---")
    db.query(WorkflowRule).delete()
    db.commit()
    print("All workflow rules deleted.")

    # Get a valid user ID from DB
    user = db.query(User).first()
    if user:
        user_id = str(user.id)
        print(f"Using valid user ID for assignment: {user_id} ({user.email})")
    else:
        user_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        print("No users found, using fallback UUID")
finally:
    db.close()

base_url = "http://127.0.0.1:8000"

def login(username, password):
    data = urllib.parse.urlencode({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/auth/login", data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))["access_token"]

token = login("vikas@example.com", "vikas") # Admin user
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Create Workflow Rule
print("\n--- 1. Creating Workflow Rule ---")
rule_payload = {
    "name": "New Lead Automation",
    "description": "Auto-assign, create task, send email, and notify on new lead.",
    "trigger_entity": "Lead",
    "trigger_event": "created",
    "is_active": True,
    "actions": [
        {
            "action_type": "assign_user",
            "action_params": {"user_id": user_id},
            "execution_order": 1
        },
        {
            "action_type": "create_task",
            "action_params": {
                "title": "Initial Follow-up Call",
                "description": "Call the new lead to understand requirements.",
                "due_in_days": 2
            },
            "execution_order": 2
        },
        {
            "action_type": "send_email",
            "action_params": {
                "subject": "Welcome to our Services!",
                "body": "Hello {{first_name}},\n\nThank you for reaching out! Our executive will contact you shortly."
            },
            "execution_order": 3
        },
        {
            "action_type": "notify_user",
            "action_params": {
                "title": "New Lead Alert",
                "message": "A new lead was generated and assigned."
            },
            "execution_order": 4
        }
    ]
}

try:
    req = urllib.request.Request(f"{base_url}/crm/workflows", data=json.dumps(rule_payload).encode('utf-8'), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        rule = json.loads(resp.read().decode('utf-8'))
        print(f"Created Workflow: {rule['name']} with {len(rule['actions'])} actions.")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

# 2. Trigger the Workflow (Create Lead)
print("\n--- 2. Triggering Workflow (Creating Lead) ---")
lead_payload = {
    "first_name": "Workflow",
    "last_name": "Test",
    "email": "workflow.test@example.com",
    "phone": "9999999999",
    "company": "Automation Inc",
    "status": "new"
}

try:
    req = urllib.request.Request(f"{base_url}/crm/leads", data=json.dumps(lead_payload).encode('utf-8'), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        lead = json.loads(resp.read().decode('utf-8'))
        print(f"Created Lead: {lead['first_name']} {lead['last_name']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

print("Waiting 3 seconds for background workflow execution...")
time.sleep(3)

# 3. Check Tasks
print("\n--- 3. Verifying Results (Tasks) ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/tasks", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        if data["total"] > 0:
            print(f"SUCCESS Found {data['total']} Tasks! Latest: '{data['items'][0]['title']}'")
        else:
            print("FAILED No Tasks found in DB!")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
