import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_me_scenarios(client: TestClient, admin_token: str):
    # 1. Test /auth/me with Authorization: Bearer <token> header
    headers = {"Authorization": f"Bearer {admin_token}"}
    response_header = client.get("/auth/me", headers=headers)
    assert response_header.status_code == 200, response_header.text
    data_header = response_header.json()
    assert data_header["email"] == "admin@example.com"

    # 2. Test /auth/me with no authentication
    response_none = client.get("/auth/me")
    assert response_none.status_code == 401
    assert response_none.json()["detail"] == "Not authenticated"
