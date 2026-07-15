import sys, os
from fastapi.testclient import TestClient
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.main import app
client = TestClient(app)
from app.db.database import SessionLocal
from app.models.user import User
db = SessionLocal()
user = db.query(User).first()
token = client.post('/auth/login', data={'username': user.email, 'password': 'password123'})
headers = {'Authorization': f'Bearer {token.json().get("access_token")}'}
resp = client.get('/crm/leads?page=1&size=10', headers=headers)
print(resp.json())
