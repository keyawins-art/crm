import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import engine
from app.models import Base

# Create all tables before any test collection/execution happens
Base.metadata.create_all(bind=engine)

from app.main import app
from app.main import limiter as main_limiter
from app.api.auth import limiter as auth_limiter
main_limiter.enabled = False
auth_limiter.enabled = False

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def admin_token(client: TestClient):
    # Log in as admin
    response = client.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
    
    # If not exists, insert directly into DB
    if response.status_code != 200:
        from app.db.database import SessionLocal
        from app.models.user import User
        from app.models.role import Role
        from app.core.security import get_password_hash
        from app.core.rbac_seed import seed_rbac_data
        
        db = SessionLocal()
        # Ensure RBAC roles and permissions exist
        seed_rbac_data(db)
        
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        admin_user = User(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password_hash=get_password_hash("admin"),
            role_id=admin_role.id if admin_role else None,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.close()
        
        response = client.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
        
    return response.json()["access_token"]
