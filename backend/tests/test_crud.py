import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal

client = TestClient(app)

def test_account_crud_lifecycle():
    db_session = SessionLocal()
    try:
        # Register an admin user to perform operations
        email = f"admin_{uuid4().hex[:8]}@example.com"
        resp = client.post("/auth/register", json={"email": email, "password": "TestPass123!", "first_name": "Ad", "last_name": "Min"})
        assert resp.status_code == 201

        from app.models import User, Role
        user = db_session.query(User).filter(User.email == email).first()
        admin_role = db_session.query(Role).filter(Role.name == "Admin").first()
        user.role_id = admin_role.id
        db_session.commit()

        resp = client.post("/auth/login", data={"username": email, "password": "TestPass123!"})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

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
        assert del_resp.status_code == 204

        # 5. GET by ID (should be 404 since it's soft deleted)
        get_del_resp = client.get(f"/crm/accounts/{account_id}", headers=headers)
        assert get_del_resp.status_code == 404

        # 6. RESTORE Account
        restore_resp = client.post(f"/crm/accounts/{account_id}/restore", headers=headers)
        assert restore_resp.status_code == 200

        # 7. GET by ID (should be 200 again)
        get_restored_resp = client.get(f"/crm/accounts/{account_id}", headers=headers)
        assert get_restored_resp.status_code == 200

        # 8. HARD DELETE Account
        hard_del_resp = client.delete(f"/crm/accounts/{account_id}/hard", headers=headers)
        assert hard_del_resp.status_code == 204

        # 9. GET by ID (should be 404 permanently)
        get_hard_del_resp = client.get(f"/crm/accounts/{account_id}", headers=headers)
        assert get_hard_del_resp.status_code == 404
    finally:
        db_session.close()
