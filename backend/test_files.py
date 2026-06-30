import urllib.request
import urllib.parse
import urllib.error
import json
import os

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

# Create a dummy pdf file for testing
dummy_pdf = "test_invoice.pdf"
with open(dummy_pdf, "w") as f:
    f.write("Dummy PDF content")

# 1. Upload File
print("\n--- 1. Testing POST /crm/files/upload ---")
# Because it's multipart/form-data, we use urllib's more advanced features or just a manual boundary
import mimetypes
boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="entity_type"\r\n\r\naccounts\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="entity_id"\r\n\r\n3fa85f64-5717-4562-b3fc-2c963f66afa6\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="category"\r\n\r\nInvoices\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{dummy_pdf}"\r\n'
    f"Content-Type: application/pdf\r\n\r\n"
    f"Dummy PDF content\r\n"
    f"--{boundary}--\r\n"
)

headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

try:
    req = urllib.request.Request(f"{base_url}/crm/files/upload", data=body.encode('utf-8'), headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        doc = json.loads(resp.read().decode('utf-8'))
        print("File Uploaded:", doc["filename"], "Category:", doc["category"])
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
    exit(1)

# Cleanup dummy file locally
os.remove(dummy_pdf)

# 2. Get Files
print("\n--- 2. Testing GET /crm/files ---")
headers["Content-Type"] = "application/json"
try:
    req = urllib.request.Request(f"{base_url}/crm/files?category=Invoices", headers=headers, method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Total Invoice Files Found:", data["total"])
        for m in data["items"]:
            print(f"- {m['filename']} (Path: {m['file_path']}, Size: {m['file_size']} bytes)")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")
