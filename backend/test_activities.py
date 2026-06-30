import urllib.request
import urllib.parse
import urllib.error
import json
from app.db.database import SessionLocal
from app.models.lead import Lead, LeadStatus

base_url = "http://127.0.0.1:8000"

# 1. Create a dummy lead directly via DB
db = SessionLocal()
try:
    lead = Lead(
        first_name="Activity",
        last_name="Test",
        email="activity.test@example.com",
        phone="555-0200",
        company="Activity Corp",
        status=LeadStatus.NEW,
        industry="Technology"
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    lead_id = str(lead.id)
finally:
    db.close()

print(f"--- Created Lead with ID: {lead_id} ---")

# 2. Login
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

# 3. Add a Note
print("\n--- Testing POST Note ---")
note_payload = json.dumps({"content": "Customer interested in buying CRM."}).encode('utf-8')
try:
    req = urllib.request.Request(f"{base_url}/crm/leads/{lead_id}/notes", data=note_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        print("Note Response:", json.loads(resp.read().decode('utf-8')))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

# 4. Add an Activity
print("\n--- Testing POST Activity ---")
activity_payload = json.dumps({
   "type":"Call",
   "subject":"Follow-up Call",
   "date":"2026-07-01T10:00:00Z"
}).encode('utf-8')
try:
    req = urllib.request.Request(f"{base_url}/crm/leads/{lead_id}/activities", data=activity_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        print("Activity Response:", json.loads(resp.read().decode('utf-8')))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

# 5. Fetch Timeline
print("\n--- Testing GET Timeline ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/leads/{lead_id}/timeline", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        timeline = json.loads(resp.read().decode('utf-8'))
        print("Timeline Entries:")
        for t in timeline:
            print(f"- {t['activity_date']} | {t['activity_type']}: {t['content']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
