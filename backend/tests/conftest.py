import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def admin_token(client: TestClient):
    # Log in as admin
    # Assuming seed.py created admin@example.com / admin
    response = client.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
    
    # If not exists, try to register it
    if response.status_code != 200:
        client.post("/auth/register", json={
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "password": "admin"
        })
        response = client.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
        
    return response.json()["access_token"]
