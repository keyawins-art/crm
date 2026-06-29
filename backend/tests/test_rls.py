import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal

client = TestClient(app)

def test_rls_sales_executive_owns_data():
    db_session = SessionLocal()
    try:
        from app.models import User, Role
        
        # Create Admin
        admin_email = f"admin_{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": admin_email, "password": "TestPass123!", "first_name": "Ad", "last_name": "Min"})
        user_admin = db_session.query(User).filter(User.email == admin_email).first()
        admin_role = db_session.query(Role).filter(Role.name == "Admin").first()
        user_admin.role_id = admin_role.id
        db_session.commit()
        
        resp = client.post("/auth/login", data={"username": admin_email, "password": "TestPass123!"})
        admin_token = resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create Sales Exec
        exec_email = f"exec_{uuid4().hex[:8]}@example.com"
        client.post("/auth/register", json={"email": exec_email, "password": "TestPass123!", "first_name": "Sa", "last_name": "Les"})
        user_exec = db_session.query(User).filter(User.email == exec_email).first()
        exec_role = db_session.query(Role).filter(Role.name == "Sales Executive").first()
        user_exec.role_id = exec_role.id
        db_session.commit()
        
        resp = client.post("/auth/login", data={"username": exec_email, "password": "TestPass123!"})
        exec_token = resp.json()["access_token"]
        exec_headers = {"Authorization": f"Bearer {exec_token}"}
        
        # 1. Admin creates a Lead
        resp = client.post("/crm/leads", headers=admin_headers, json={"first_name": "Admin", "last_name": "Lead"})
        assert resp.status_code == 201
        admin_lead_id = resp.json()["id"]
        
        # 2. Sales Exec tries to GET Admin's lead
        resp = client.get(f"/crm/leads/{admin_lead_id}", headers=exec_headers)
        assert resp.status_code == 404  # RLS should filter it out, looking like it doesn't exist
        
        # 3. Sales Exec creates a Lead
        resp = client.post("/crm/leads", headers=exec_headers, json={"first_name": "Exec", "last_name": "Lead"})
        assert resp.status_code == 201
        exec_lead_id = resp.json()["id"]
        
        # 4. Sales Exec can GET their own lead
        resp = client.get(f"/crm/leads/{exec_lead_id}", headers=exec_headers)
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Exec"
        
        # 5. Admin can GET Sales Exec's lead
        resp = client.get(f"/crm/leads/{exec_lead_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Exec"
        
        # 6. Admin can update Exec's lead
        resp = client.put(f"/crm/leads/{exec_lead_id}", headers=admin_headers, json={"company": "Changed by Admin"})
        assert resp.status_code == 200
        
        # 7. Exec tries to delete Admin's lead
        resp = client.delete(f"/crm/leads/{admin_lead_id}", headers=exec_headers)
        assert resp.status_code == 404
        
        # 8. Exec list leads only shows their own lead
        resp = client.get("/crm/leads", headers=exec_headers)
        assert resp.status_code == 200
        leads = resp.json()
        assert len(leads) >= 1
        assert all(lead["created_by_id"] == str(user_exec.id) or lead["assigned_to_id"] == str(user_exec.id) for lead in leads)

    finally:
        db_session.close()
