import urllib.request
import urllib.parse
import urllib.error
import json

base_url = "http://127.0.0.1:8000"
username = "vikas@example.com"
password = "vikas"

def register():
    print(f"Registering {username}...")
    req = urllib.request.Request(
        f"{base_url}/auth/register",
        data=json.dumps({
            "email": username,
            "password": password,
            "first_name": "Vikas",
            "last_name": "Prajapat",
            "phone": "1234567890"
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        urllib.request.urlopen(req)
        print("Registration successful!")
    except Exception as e:
        print(f"Registration failed (might already exist): {e}")

def login():
    data = urllib.parse.urlencode({"username": username, "password": password}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/auth/login", data=data)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            return resp_data["access_token"]
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None
        raise e

# 1. Login or Register
token = login()
if not token:
    register()
    token = login()

if not token:
    print("Could not obtain token!")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

def run_combined_test():
    params = {
        "search": "o",
        "industry": "technology",
        "page": 1,
        "size": 5,
        "sort": "name",
        "order": "asc"
    }
    print(f"\n--- Testing Combined Parameters via HTTP API ---")
    print(f"Parameters: {params}")
    
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{base_url}/crm/accounts?{query}", headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            names = [item["name"] for item in data.get("items", [])]
            print(f"HTTP Results (Total Items: {data.get('total')}, Page: {data.get('page')}):")
            print(f"Company Names: {names}")
    except Exception as e:
        print(f"Error: {e}")

run_combined_test()

