import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal

client = TestClient(app)

def test_account_crud_lifecycle(client: TestClient, admin_token: str):
    db_session = SessionLocal()
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. CREATE Account
        create_resp = client.post("/crm/accounts", headers=headers, json={"name": "CRUD Test Account", "industry": "technology"})
        assert create_resp.status_code == 201
        account_id = create_resp.json()["id"]

        # 2. GET by ID
        get_resp = client.get(f"/crm/accounts/{account_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "CRUD Test Account"

        # 3. PUT (Update) Account
        put_resp = client.put(f"/crm/accounts/{account_id}", headers=headers, json={"name": "Updated CRUD Account"})
        assert put_resp.status_code == 200
        assert put_resp.json()["name"] == "Updated CRUD Account"
        
        # 4. DELETE (Soft Delete) Account
        del_resp = client.delete(f"/crm/accounts/{account_id}", headers=headers)
        assert del_resp.status_code in [200, 204]

        # 5. GET by ID (should be 404 since it's soft deleted)
        get_del_resp = client.get(f"/crm/accounts/{account_id}", headers=headers)
        assert get_del_resp.status_code == 404
    finally:
        db_session.close()
