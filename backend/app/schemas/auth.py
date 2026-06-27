from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class AuthConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(AuthConfig):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None


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
