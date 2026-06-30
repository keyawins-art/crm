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

def test_register_duplicate(client: TestClient, admin_token: str):
    # Try registering admin again
    payload = {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "admin"
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
