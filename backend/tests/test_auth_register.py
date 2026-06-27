import uuid
from fastapi.testclient import TestClient

from app.main import app


def test_register_returns_tokens():
    client = TestClient(app)
    unique_email = f"regression_{uuid.uuid4().hex[:10]}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "first_name": "Regression",
            "last_name": "User",
            "phone": "1234567890",
            "password": "StrongPass123!",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
