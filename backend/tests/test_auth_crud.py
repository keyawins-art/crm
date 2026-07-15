import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

def test_login_success(client: TestClient, admin_token: str):
    # Admin is created by conftest, we can log in with it
    response = client.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_failure(client: TestClient):
    response = client.post("/auth/login", data={"username": "fake@fake.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]

def test_invite_duplicate(client: TestClient, admin_token: str):
    # Try inviting admin again
    payload = {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "1234567890"
    }
    response = client.post(
        "/auth/invite", 
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
