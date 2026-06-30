import urllib.request
import urllib.parse
import urllib.error
import json

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

print("\n--- 1. Testing POST Lead (Welcome Email) ---")
lead_payload = json.dumps({
    "first_name": "Email",
    "last_name": "Test",
    "email": "email.test@example.com",
    "company": "Email Corp",
    "industry": "Technology"
}).encode('utf-8')

try:
    req = urllib.request.Request(f"{base_url}/crm/leads", data=lead_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        lead = json.loads(resp.read().decode('utf-8'))
        print("Lead Created:", lead["id"])
        lead_id = lead["id"]
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

print("\n--- 2. Testing POST Activity (Follow-up Email) ---")
activity_payload = json.dumps({
   "type":"email",
   "subject":"Just checking in",
   "date":"2026-07-01T10:00:00Z"
}).encode('utf-8')

try:
    req = urllib.request.Request(f"{base_url}/crm/leads/{lead_id}/activities", data=activity_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        act = json.loads(resp.read().decode('utf-8'))
        print("Activity Added:", act["id"])
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

print("\n(Check your uvicorn terminal to see the Mock Email outputs!)")
