from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class AuthConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(AuthConfig):
    email: EmailStr
    password: str


class TokenResponse(AuthConfig):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(AuthConfig):
    refresh_token: str


class MeResponse(AuthConfig):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None


# ---------------------------------------------------------------------------
# Invite-only registration (replaces public RegisterRequest)
# ---------------------------------------------------------------------------
class InviteRequest(AuthConfig):
    """Admin sends this to create a new invited user."""
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role_id: Optional[UUID] = None


class InviteResponse(AuthConfig):
    user_id: UUID
    email: EmailStr
    invite_token: str
    message: str


class AcceptInviteRequest(AuthConfig):
    """New user sends this to set their password and activate their account."""
    invite_token: str
    password: str
