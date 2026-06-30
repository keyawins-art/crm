import urllib.request
import urllib.parse
import urllib.error
import json
import time

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

# 1. Send Email Manually
print("\n--- 1. Testing POST /crm/emails/send ---")
payload = json.dumps({
    "recipient": "client@example.com",
    "subject": "Follow-up regarding your quotation",
    "body": "Hello, I wanted to follow up on the quotation sent earlier. Let me know if you have any questions."
}).encode('utf-8')

try:
    req = urllib.request.Request(f"{base_url}/crm/emails/send", data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        print("API Response:", result)
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

print("Waiting a second for background task to complete...")
time.sleep(1)

# 2. Get Email Logs
print("\n--- 2. Testing GET /crm/email-logs ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/email-logs", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Total Email Logs Found:", data["total"])
        for m in data["items"]:
            print(f"- To: {m['recipient']} | Subject: {m['subject']} | Status: {m['status']} | Time: {m['sent_time']}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
