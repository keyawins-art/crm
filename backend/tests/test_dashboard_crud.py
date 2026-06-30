import pytest
from fastapi.testclient import TestClient

def test_get_dashboard_success(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/crm/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert "contacts" in data
    assert "leads" in data

def test_get_dashboard_unauthorized(client: TestClient):
    response = client.get("/crm/dashboard")
    assert response.status_code == 401

def test_get_dashboard_kpi_success(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/crm/dashboard/kpi", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "conversion_rate" in data
    assert "win_rate" in data
    assert "lost_rate" in data
