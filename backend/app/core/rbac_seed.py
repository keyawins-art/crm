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
    "tickets":       ["create", "read", "update", "delete"],
    "kb":            ["create", "read", "update", "delete"],
    "documents":     ["create", "read", "delete"],
    "sales_orders":  ["create", "read", "update", "delete"],
    "invoices":      ["create", "read", "update"],
    "payments":      ["create", "read"],
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
        "products:*",
        "sales_orders:*",
        "invoices:*",
        "payments:*",
        "documents:*",
        "users:read",
    ],
    "Sales Executive": [
        "leads:create", "leads:read", "leads:update",
        "contacts:create", "contacts:read", "contacts:update",
        "accounts:read",
        "accounts:update",
        "opportunities:create", "opportunities:read", "opportunities:update",
        "quotations:create", "quotations:read", "quotations:update",
        "sales_orders:create", "sales_orders:read", "sales_orders:update",
        "invoices:read",
        "documents:create", "documents:read",
        "products:read",
        "users:read",
        "kb:read",
        "tickets:read",
    ],
    "Support": [
        "accounts:read",
        "contacts:read",
        "leads:read",
        "tickets:create", "tickets:read", "tickets:update", "tickets:delete",
        "kb:read",
        "documents:read",
    ],
}

# Roles whose permissions are fully managed by this seeder.
# On each run, any permission NOT in the spec above is removed.
SYSTEM_MANAGED_ROLES = {"Admin", "Sales Manager", "Sales Executive", "Support"}


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

    # --- 3. Reconcile role-permission mappings ---
    for role_name, perm_spec in ROLE_PERMISSIONS.items():
        role = roles[role_name]
        needed = _expand_permissions(perm_spec, all_perm_names)

        # Build lookup of existing mappings for this role
        existing_mappings = {
            rp.permission_id: rp
            for rp in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()
        }

        # Reverse lookup: permission id → name
        perm_id_to_name = {p.id: name for name, p in all_permissions.items()}

        # Add missing permissions
        needed_ids = set()
        for perm_name in needed:
            perm = all_permissions.get(perm_name)
            if perm:
                needed_ids.add(perm.id)
                if perm.id not in existing_mappings:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))

        # Remove stale permissions for system-managed roles
        if role_name in SYSTEM_MANAGED_ROLES:
            for perm_id, rp in existing_mappings.items():
                if perm_id not in needed_ids:
                    perm_display = perm_id_to_name.get(perm_id, str(perm_id))
                    print(f"  Removing stale permission '{perm_display}' from role '{role_name}'")
                    db.delete(rp)

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
