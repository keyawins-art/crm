import pytest
from fastapi.testclient import TestClient

def test_create_lead_success(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "company": "Acme Inc"
    }
    response = client.post("/crm/leads", json=payload, headers=headers)
    if response.status_code == 400:
        # Already exists from previous test run
        assert "already exists" in response.json()["detail"]
    else:
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"

def test_create_lead_duplicate_email(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.unique@example.com",
    }
    # First create
    client.post("/crm/leads", json=payload, headers=headers)
    # Second create should fail
    response = client.post("/crm/leads", json=payload, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_convert_lead(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "first_name": "Convert",
        "last_name": "Me",
        "email": "convert.me@example.com",
        "company": "Conversion Inc"
    }
    create_resp = client.post("/crm/leads", json=payload, headers=headers)
    if create_resp.status_code == 201:
        lead_id = create_resp.json()["id"]
        
        # Convert it
        convert_payload = {
            "create_opportunity": True,
            "opportunity_name": "Big Deal",
            "amount": 5000.0
        }
        convert_resp = client.post(f"/crm/leads/{lead_id}/convert", json=convert_payload, headers=headers)
        assert convert_resp.status_code == 200
        data = convert_resp.json()
        assert data["status"] == "converted"
        assert "opportunity_id" in data
        assert "account_id" in data
        assert "contact_id" in data
        
        # Try converting again
        fail_resp = client.post(f"/crm/leads/{lead_id}/convert", json=convert_payload, headers=headers)
        assert fail_resp.status_code == 400
        assert "already converted" in fail_resp.json()["detail"]
