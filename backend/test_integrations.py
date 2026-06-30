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

token = login("vikas@example.com", "vikas") # Admin user
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Fetch integrations list (initial seed)
print("\n--- 1. Listing Integrations ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/integrations", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Total Integrations Configured: {len(data)}")
        for provider in data[:3]:
            print(f"- {provider['provider_name']}: {provider['status']} (Enabled: {provider['is_enabled']})")
except urllib.error.HTTPError as e:
    print(f"Error listing: {e.code} - {e.read().decode('utf-8')}")

# 2. Connect Stripe
print("\n--- 2. Connecting Stripe Integration ---")
payload = {"credentials": {"api_key": "sk_test_12345"}}
try:
    req = urllib.request.Request(
        f"{base_url}/crm/integrations/stripe/connect",
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"Stripe Connected: status={res['status']}, is_enabled={res['is_enabled']}")
except urllib.error.HTTPError as e:
    print(f"Error connecting: {e.code} - {e.read().decode('utf-8')}")

# 3. Test Stripe Integration
print("\n--- 3. Testing Stripe Integration ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/integrations/stripe/test", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Test Stripe Response:", res)
except urllib.error.HTTPError as e:
    print(f"Error testing: {e.code} - {e.read().decode('utf-8')}")

# 4. Disconnect Stripe
print("\n--- 4. Disconnecting Stripe Integration ---")
try:
    req = urllib.request.Request(f"{base_url}/crm/integrations/stripe/disconnect", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"Stripe Disconnected: status={res['status']}, is_enabled={res['is_enabled']}")
except urllib.error.HTTPError as e:
    print(f"Error disconnecting: {e.code} - {e.read().decode('utf-8')}")
