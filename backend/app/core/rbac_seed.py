"""
Idempotent RBAC seeder — creates default roles, permissions, and mappings.

Run:  python -m app.core.rbac_seed
Or call seed_rbac_data(db) from app startup.
"""

from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models import Role, Permission, RolePermission


# ---------------------------------------------------------------------------
# Permission definitions: (resource, action)
# ---------------------------------------------------------------------------
RESOURCES_ACTIONS = {
    "accounts":      ["create", "read", "update", "delete"],
    "contacts":      ["create", "read", "update", "delete"],
    "leads":         ["create", "read", "update", "delete"],
    "products":      ["create", "read", "update", "delete"],
    "opportunities": ["create", "read", "update", "delete"],
    "quotations":    ["create", "read", "update", "delete"],
    "users":         ["create", "read", "update", "delete"],
}

# ---------------------------------------------------------------------------
# Role → permission mapping
# ---------------------------------------------------------------------------
ROLE_PERMISSIONS = {
    "Admin": "*",  # all permissions
    "Sales Manager": [
        "accounts:*",
        "contacts:*",
        "leads:*",
        "opportunities:*",
        "quotations:*",
    ],
    "Sales Executive": [
        "leads:create", "leads:read", "leads:update",
        "contacts:create", "contacts:read", "contacts:update",
        "accounts:read",
        "opportunities:read",
        "quotations:read",
    ],
    "Support": [
        "accounts:read",
        "contacts:read",
        "leads:read",
    ],
}


def _expand_permissions(spec, all_permission_names: set) -> set:
    """Expand wildcard patterns like '*' and 'accounts:*'."""
    if spec == "*":
        return set(all_permission_names)

    result = set()
    for entry in spec:
        if entry.endswith(":*"):
            resource = entry.split(":")[0]
            result.update(
                name for name in all_permission_names
                if name.startswith(f"{resource}:")
            )
        else:
            result.add(entry)
    return result


def seed_rbac_data(db: Session) -> None:
    """Create roles, permissions, and mappings. Idempotent — safe to re-run."""

    # --- 1. Upsert permissions ---
    all_permissions: dict[str, Permission] = {}

    for resource, actions in RESOURCES_ACTIONS.items():
        for action in actions:
            perm_name = f"{resource}:{action}"
            existing = db.query(Permission).filter(Permission.name == perm_name).first()
            if not existing:
                existing = Permission(
                    name=perm_name,
                    resource=resource,
                    action=action,
                    description=f"{action.capitalize()} {resource}",
                )
                db.add(existing)
                db.flush()
            all_permissions[perm_name] = existing

    # --- 2. Upsert roles ---
    all_perm_names = set(all_permissions.keys())
    roles: dict[str, Role] = {}

    for role_name, perm_spec in ROLE_PERMISSIONS.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=f"{role_name} role",
            )
            db.add(role)
            db.flush()
        roles[role_name] = role

    # --- 3. Upsert role-permission mappings ---
    for role_name, perm_spec in ROLE_PERMISSIONS.items():
        role = roles[role_name]
        needed = _expand_permissions(perm_spec, all_perm_names)

        # Get existing mappings for this role
        existing_perm_ids = {
            rp.permission_id
            for rp in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()
        }

        for perm_name in needed:
            perm = all_permissions[perm_name]
            if perm.id not in existing_perm_ids:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
    print(f"RBAC seed complete: {len(all_permissions)} permissions, {len(roles)} roles.")


# ---------------------------------------------------------------------------
# CLI entry-point:  python -m app.core.rbac_seed
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_rbac_data(db)
    finally:
        db.close()
