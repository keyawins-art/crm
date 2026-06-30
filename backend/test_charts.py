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

endpoints = [
    ("/crm/reports/monthly-leads", "Monthly Leads"),
    ("/crm/reports/revenue", "Revenue"),
    ("/crm/reports/funnel", "Sales Funnel")
]

for endpoint, name in endpoints:
    print(f"\n--- Testing GET {name} ---")
    try:
        req = urllib.request.Request(f"{base_url}{endpoint}", headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            print(f"{name} Response:", json.loads(resp.read().decode('utf-8')))
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode('utf-8')}")
