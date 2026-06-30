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

# 1. Trigger Reminders
print("\n--- 1. Testing POST /crm/system/trigger-reminders ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/system/trigger-reminders", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print("API Response:", result)
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

# 2. Get Notifications
print("\n--- 2. Testing GET /crm/notifications ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/notifications", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Total Notifications Found:", data["total"])
        for n in data["items"][:5]: # Show top 5
            print(f"- [{n['notification_type']}] {n['title']}: {n['message']} (Read: {n['is_read']})")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
