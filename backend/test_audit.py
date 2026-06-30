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

print("\n--- Testing GET Audit Logs ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/audit-logs", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        logs = json.loads(resp.read().decode('utf-8'))
        print(f"Total Logs Found: {len(logs)}")
        for log in logs[:5]:
            print(f"- {log['created_at']} | {log['details']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
