"""
RBAC integration tests.

Tests permission enforcement on CRM endpoints for different roles:
  - Admin → full access
  - Sales Executive → limited access
  - Support → read-only on some resources
  - No role → 403 on everything
"""

import uuid
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import SessionLocal
from app.core.rbac_seed import seed_rbac_data
from app.core.security import get_password_hash
from app.models import Role, User, UserStatus

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_once():
    """Ensure RBAC seed data exists (idempotent)."""
    db: Session = SessionLocal()
    try:
        seed_rbac_data(db)
    finally:
        db.close()


def _create_user_with_role(role_name: str | None) -> dict:
    """Create a user in the DB with the given role and return {user, token}."""
    db: Session = SessionLocal()
    try:
        role = None
        if role_name:
            role = db.query(Role).filter(Role.name == role_name).first()

        email = f"test_{uuid.uuid4().hex[:10]}@example.com"
        user = User(
            email=email,
            first_name="Test",
            last_name=role_name or "NoRole",
            phone="0000000000",
            password_hash=get_password_hash("TestPass123!"),
            is_active=True,
            role_id=role.id if role else None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Login to get a token
        resp = client.post("/auth/login", data={"username": email, "password": "TestPass123!"})
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]

        return {"user": user, "token": token, "email": email}
    finally:
        db.close()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures (module-level setup)
# ---------------------------------------------------------------------------

# Seed roles & permissions once before all tests
_seed_once()

_admin = _create_user_with_role("Admin")
_sales_exec = _create_user_with_role("Sales Executive")
_support = _create_user_with_role("Support")
_no_role = _create_user_with_role(None)


# ---------------------------------------------------------------------------
# Tests: Admin — full access
# ---------------------------------------------------------------------------

class TestAdminAccess:
    """Admin should have access to all CRM endpoints."""

    def test_admin_can_create_account(self):
        resp = client.post(
            "/crm/accounts",
            json={"name": f"AdminAccount_{uuid.uuid4().hex[:6]}"},
            headers=_auth_header(_admin["token"]),
        )
        assert resp.status_code == 201, resp.text

    def test_admin_can_list_accounts(self):
        resp = client.get(
            "/crm/accounts",
            headers=_auth_header(_admin["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_admin_can_create_product(self):
        resp = client.post(
            "/crm/products",
            json={"name": f"AdminProduct_{uuid.uuid4().hex[:6]}"},
            headers=_auth_header(_admin["token"]),
        )
        assert resp.status_code == 201, resp.text

    def test_admin_can_list_users(self):
        resp = client.get(
            "/crm/users",
            headers=_auth_header(_admin["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_admin_can_create_lead(self):
        resp = client.post(
            "/crm/leads",
            json={"first_name": "AdminLead", "last_name": "Test"},
            headers=_auth_header(_admin["token"]),
        )
        assert resp.status_code == 201, resp.text


# ---------------------------------------------------------------------------
# Tests: Sales Executive — limited access
# ---------------------------------------------------------------------------

class TestSalesExecutiveAccess:
    """Sales Executive can create/read leads and contacts but NOT products/users."""

    def test_can_create_lead(self):
        resp = client.post(
            "/crm/leads",
            json={"first_name": "ExecLead", "last_name": "Test"},
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 201, resp.text

    def test_can_read_leads(self):
        resp = client.get(
            "/crm/leads",
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_can_create_contact(self):
        resp = client.post(
            "/crm/contacts",
            json={"first_name": "ExecContact", "last_name": "Test"},
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 201, resp.text

    def test_can_read_accounts(self):
        resp = client.get(
            "/crm/accounts",
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_cannot_create_product(self):
        resp = client.post(
            "/crm/products",
            json={"name": "Blocked"},
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 403, resp.text
        assert "Permission denied" in resp.json()["detail"]

    def test_cannot_create_account(self):
        resp = client.post(
            "/crm/accounts",
            json={"name": "Blocked"},
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 403, resp.text

    def test_can_list_users(self):
        resp = client.get(
            "/crm/users",
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_can_read_products(self):
        resp = client.get(
            "/crm/products",
            headers=_auth_header(_sales_exec["token"]),
        )
        assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# Tests: Support — read-only on accounts, contacts, leads
# ---------------------------------------------------------------------------

class TestSupportAccess:
    """Support can only read accounts, contacts, leads. No write. No products."""

    def test_can_read_accounts(self):
        resp = client.get(
            "/crm/accounts",
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_can_read_contacts(self):
        resp = client.get(
            "/crm/contacts",
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_can_read_leads(self):
        resp = client.get(
            "/crm/leads",
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 200, resp.text

    def test_cannot_create_account(self):
        resp = client.post(
            "/crm/accounts",
            json={"name": "Blocked"},
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 403, resp.text

    def test_cannot_create_lead(self):
        resp = client.post(
            "/crm/leads",
            json={"first_name": "Blocked", "last_name": "User"},
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 403, resp.text

    def test_cannot_read_products(self):
        resp = client.get(
            "/crm/products",
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 403, resp.text

    def test_cannot_read_opportunities(self):
        resp = client.get(
            "/crm/opportunities",
            headers=_auth_header(_support["token"]),
        )
        assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Tests: No role assigned
# ---------------------------------------------------------------------------

class TestNoRoleAccess:
    """A user with no role should get 403 on all protected endpoints."""

    def test_cannot_list_accounts(self):
        resp = client.get(
            "/crm/accounts",
            headers=_auth_header(_no_role["token"]),
        )
        assert resp.status_code == 403, resp.text
        assert "No role assigned" in resp.json()["detail"]

    def test_cannot_create_lead(self):
        resp = client.post(
            "/crm/leads",
            json={"first_name": "NoRole", "last_name": "User"},
            headers=_auth_header(_no_role["token"]),
        )
        assert resp.status_code == 403, resp.text

    def test_cannot_read_products(self):
        resp = client.get(
            "/crm/products",
            headers=_auth_header(_no_role["token"]),
        )
        assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Tests: Unauthenticated — no token at all
# ---------------------------------------------------------------------------

class TestUnauthenticatedAccess:
    """No token → 401 on all CRM endpoints."""

    def test_accounts_requires_auth(self):
        resp = client.get("/crm/accounts")
        assert resp.status_code == 401

    def test_leads_requires_auth(self):
        resp = client.post("/crm/leads", json={"first_name": "X", "last_name": "Y"})
        assert resp.status_code == 401

    def test_health_is_public(self):
        resp = client.get("/crm/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests: /auth/me returns role
# ---------------------------------------------------------------------------

class TestMeEndpointRole:
    """Verify /auth/me now includes the role field."""

    def test_admin_me_shows_role(self):
        resp = client.get("/auth/me", headers=_auth_header(_admin["token"]))
        assert resp.status_code == 200
        assert resp.json()["role"] == "Admin"

    def test_no_role_me_shows_null(self):
        resp = client.get("/auth/me", headers=_auth_header(_no_role["token"]))
        assert resp.status_code == 200
        assert resp.json()["role"] is None
