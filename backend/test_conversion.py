from app.db.database import SessionLocal
from app.models.lead import Lead, LeadSourceType, LeadStatus
import urllib.request
import urllib.parse
import urllib.error
import json

base_url = "http://127.0.0.1:8000"
db = SessionLocal()
try:
    # 1. Create a dummy lead
    lead = Lead(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="555-0100",
        company="Doe Industries",
        status=LeadStatus.NEW,
        industry="Technology",
        annual_revenue=1000000
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    lead_id = str(lead.id)
    print(f"Created Lead with ID: {lead_id}")
finally:
    db.close()

# 2. Login to get token
def login(username, password):
    data = urllib.parse.urlencode({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/auth/login", data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))["access_token"]

token = login("vikas@example.com", "vikas")

# 3. Call convert API
print("\n--- Testing Lead Conversion ---")
payload = {
    "create_opportunity": True,
    "opportunity_name": "CRM Software Deal",
    "amount": 500000
}
data = json.dumps(payload).encode('utf-8')
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

req = urllib.request.Request(f"{base_url}/crm/leads/{lead_id}/convert", data=data, headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        print(f"Status: {resp.status}")
        print("Response:", json.loads(resp.read().decode('utf-8')))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
