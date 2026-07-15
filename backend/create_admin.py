#!/usr/bin/env python3
"""
Create or reset an admin user for CRM.

Reads credentials from environment variables or CLI arguments — never from
hardcoded values.

Usage:
    # Via environment variables (recommended for CI/scripts):
    ADMIN_EMAIL=admin@yourco.com ADMIN_PASSWORD='S3cure!Pass#2026' python create_admin.py

    # Via CLI arguments:
    python create_admin.py --email admin@yourco.com --password 'S3cure!Pass#2026'
"""
import argparse
import os
import re
import sys

sys.path.insert(0, ".")

from app.core.security import get_password_hash
from app.db.database import SessionLocal
from app.models.user import User
from app.models.role import Role


# ---------------------------------------------------------------------------
# Password policy
# ---------------------------------------------------------------------------
MIN_PASSWORD_LENGTH = 12

def _check_password_strength(password: str) -> list[str]:
    """Return a list of policy violations (empty list = strong password)."""
    issues = []
    if len(password) < MIN_PASSWORD_LENGTH:
        issues.append(f"Must be at least {MIN_PASSWORD_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        issues.append("Must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        issues.append("Must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        issues.append("Must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\;'/`~]", password):
        issues.append("Must contain at least one special character")
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Create or reset CRM admin user")
    parser.add_argument("--email", default=os.getenv("ADMIN_EMAIL"), help="Admin email (or set ADMIN_EMAIL env var)")
    parser.add_argument("--password", default=os.getenv("ADMIN_PASSWORD"), help="Admin password (or set ADMIN_PASSWORD env var)")
    args = parser.parse_args()

    email = args.email
    password = args.password

    if not email:
        print("ERROR: Admin email is required. Pass --email or set ADMIN_EMAIL env var.")
        sys.exit(1)
    if not password:
        print("ERROR: Admin password is required. Pass --password or set ADMIN_PASSWORD env var.")
        sys.exit(1)

    # Enforce password policy
    issues = _check_password_strength(password)
    if issues:
        print("ERROR: Password does not meet security policy:")
        for issue in issues:
            print(f"  • {issue}")
        sys.exit(1)

    email = email.strip().lower()

    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "System Administrator").first()
        if not admin_role:
            admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = db.query(Role).first()

        admin = db.query(User).filter(User.email == email).first()
        if admin:
            admin.password_hash = get_password_hash(password)
            print(f"Reset password for {email}")
        else:
            admin = User(
                email=email,
                first_name="Admin",
                last_name="CRM",
                password_hash=get_password_hash(password),
                is_active=True,
                role_id=admin_role.id if admin_role else None,
            )
            db.add(admin)
            print(f"Created admin user: {email}")

        db.commit()
        print("Done! Admin account is ready.")
        # NOTE: Password is intentionally NOT printed.
    finally:
        db.close()


if __name__ == "__main__":
    main()
