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

# 1. Create a Meeting
print("\n--- 1. Testing POST /crm/meetings ---")
start = (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"
end = (datetime.utcnow() + timedelta(days=2, hours=1)).isoformat() + "Z"

payload = json.dumps({
    "subject": "Product Demo",
    "location": "Zoom",
    "meeting_link": "https://zoom.us/j/123456789",
    "start_time": start,
    "end_time": end,
    "attendees": ["client@example.com", "manager@example.com"],
    "notes": "Discussing enterprise features",
    "status": "scheduled"
}).encode('utf-8')

try:
    req = urllib.request.Request(f"{base_url}/crm/meetings", data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        meet = json.loads(resp.read().decode('utf-8'))
        meet_id = meet["id"]
        print("Meeting Created:", meet_id, "| Subject:", meet["subject"])
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

# 2. Get Meetings
print("\n--- 2. Testing GET /crm/meetings ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/meetings", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Total Meetings Found:", data["total"])
        for m in data["items"]:
            print(f"- {m['subject']} at {m['start_time']} (Status: {m['status']})")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
