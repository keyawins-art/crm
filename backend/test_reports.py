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
    "Authorization": f"Bearer {token}"
}

endpoints = [
    "/crm/reports/leads",
    "/crm/reports/opportunities",
    "/crm/reports/users",
    "/crm/reports/charts/lead-sources",
    "/crm/reports/charts/win-loss",
    "/crm/dashboard"
]

for ep in endpoints:
    print(f"\n--- Testing GET {ep} ---")
    try:
        req = urllib.request.Request(f"{base_url}{ep}", headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Response:", json.dumps(data, indent=2)[:500]) # Print first 500 chars to avoid spam
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode('utf-8')}")
