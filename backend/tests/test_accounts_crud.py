import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

def test_create_account_success(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Test Corp",
        "industry": "technology",
        "annual_revenue": 1000000.0,
    }
    response = client.post("/crm/accounts", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Corp"
    assert "id" in data

def test_create_account_unauthorized(client: TestClient):
    payload = {"name": "Test Corp"}
    response = client.post("/crm/accounts", json=payload)
    assert response.status_code == 401

def test_create_account_validation_error(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"industry": "technology"} # missing required 'name'
    response = client.post("/crm/accounts", json=payload, headers=headers)
    assert response.status_code == 422

def test_get_account_not_found(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    fake_id = str(uuid4())
    response = client.get(f"/crm/accounts/{fake_id}", headers=headers)
    assert response.status_code == 404

def test_list_accounts(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/crm/accounts?page=1&size=10", headers=headers)
    assert response.status_code == 200
    assert "items" in response.json()
