import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_me_scenarios():
    # Register a new unique user
    unique_email = f"user_{uuid.uuid4().hex[:10]}@example.com"
    reg_response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "first_name": "Test",
            "last_name": "User",
            "phone": "9876543210",
            "password": "SecurePassword123!",
        },
    )
    assert reg_response.status_code == 201, reg_response.text
    tokens = reg_response.json()
    access_token = tokens["access_token"]

    # 1. Test /auth/me with Authorization: Bearer <token> header
    headers = {"Authorization": f"Bearer {access_token}"}
    response_header = client.get("/auth/me", headers=headers)
    assert response_header.status_code == 200, response_header.text
    data_header = response_header.json()
    assert data_header["email"] == unique_email

    # 2. Test /auth/me with no authentication
    response_none = client.get("/auth/me")
    assert response_none.status_code == 401
    assert response_none.json()["detail"] == "Not authenticated"
