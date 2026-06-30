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

# 1. Get Calendar
print("\n--- 1. Testing GET /crm/calendar ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/calendar", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        events = json.loads(resp.read().decode('utf-8'))
        print("Total Calendar Events Found:", len(events))
        for e in events:
            print(f"- [{e['type'].upper()}] {e['title']} @ {e['start_time']} (Status: {e['status']})")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
