import pytest
from fastapi.testclient import TestClient

def test_get_dashboard_stats_success(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/dashboard/stats", headers=headers)
    assert response.status_code == 200

def test_get_dashboard_unauthorized(client: TestClient):
    response = client.get("/dashboard/stats")
    assert response.status_code == 401
