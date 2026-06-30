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

# 1. Create a Call
print("\n--- 1. Testing POST /crm/calls ---")
follow_up = (datetime.utcnow() + timedelta(days=2)).isoformat() + "Z"

payload = json.dumps({
    "phone_number": "+1234567890",
    "call_type": "outbound",
    "duration": 350,
    "outcome": "Connected",
    "recording_url": "https://s3.aws.com/recordings/call_123.mp3",
    "follow_up_date": follow_up
}).encode('utf-8')

try:
    req = urllib.request.Request(f"{base_url}/crm/calls", data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        call = json.loads(resp.read().decode('utf-8'))
        call_id = call["id"]
        print("Call Logged:", call_id, "| Number:", call["phone_number"])
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

# 2. Get Calls
print("\n--- 2. Testing GET /crm/calls ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/calls", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Total Calls Found:", data["total"])
        for c in data["items"]:
            print(f"- {c['phone_number']} (Outcome: {c['outcome']}, Duration: {c['duration']}s)")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
