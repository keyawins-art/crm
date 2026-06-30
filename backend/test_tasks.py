import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime, timedelta

base_url = "http://127.0.0.1:8000"

def login(username, password):
    data = urllib.parse.urlencode({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/auth/login", data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))["access_token"]

token = login("vikas@example.com", "vikas")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Create a Task
print("\n--- 1. Testing POST /crm/tasks ---")
future_date = (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"
task_payload = json.dumps({
    "title": "Call Client to follow up",
    "description": "Need to discuss the new quotation.",
    "due_date": future_date,
    "priority": "high",
    "status": "pending",
    "reminder_time": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
}).encode('utf-8')

try:
    req = urllib.request.Request(f"{base_url}/crm/tasks", data=task_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        task = json.loads(resp.read().decode('utf-8'))
        task_id = task["id"]
        print("Task Created:", task_id, "| Title:", task["title"])
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

# 2. Get Tasks
print("\n--- 2. Testing GET /crm/tasks ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/tasks", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Total Tasks Found:", data["total"])
        for t in data["items"]:
            print(f"- {t['title']} (Priority: {t['priority']}, Status: {t['status']})")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

# 3. Update Task
print("\n--- 3. Testing PUT /crm/tasks/{id} ---")
update_payload = json.dumps({
    "status": "in_progress"
}).encode('utf-8')
try:
    req = urllib.request.Request(f"{base_url}/crm/tasks/{task_id}", data=update_payload, headers=headers, method="PUT")
    with urllib.request.urlopen(req) as resp:
        updated = json.loads(resp.read().decode('utf-8'))
        print(f"Task Updated! New Status: {updated['status']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

# 4. Delete Task
print("\n--- 4. Testing DELETE /crm/tasks/{id} ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/tasks/{task_id}", headers=headers, method="DELETE")
    with urllib.request.urlopen(req) as resp:
        print("Task deleted successfully (Status 204).")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
