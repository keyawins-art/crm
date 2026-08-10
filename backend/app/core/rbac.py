"""
RBAC dependency factory for FastAPI endpoints.

Usage:
    from app.core.rbac import require_permission

    @router.post("/accounts")
    def create_account(
        current_user: User = Depends(require_permission("accounts:create")),
        ...
    ):
"""

from fastapi import Depends, HTTPException, status

from app.api.auth import get_current_user
from app.models import User


def require_permission(permission_name: str):
    """
    Returns a FastAPI dependency that verifies the authenticated user
    holds the specified permission via their role.

    Raises 403 if:
      - User has no role assigned
      - User's role does not include the required permission
    """

    def _check_permission(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned to this user",
            )

        # Admin & System Administrator roles have full access to all features
        if current_user.role and ("admin" in current_user.role.name.lower() or current_user.role.name == "System Administrator"):
            return current_user

        user_permissions = {p.name for p in current_user.role.permissions}

        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_name}",
            )

        return current_user

    return _check_permission
