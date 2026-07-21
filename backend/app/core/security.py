import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

# Ensure .env is loaded before reading any config
_env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_env_path)

# ---------------------------------------------------------------------------
# SECRET_KEY — fail-fast if missing or left at a known-insecure default
# ---------------------------------------------------------------------------
_INSECURE_DEFAULTS = {
    "change-me-in-production",
    "super-secret-key-change-in-production",
    "12345",
    "",
}

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY in _INSECURE_DEFAULTS:
    raise RuntimeError(
        "SECRET_KEY is missing or set to a known-insecure default. "
        "Set a strong, random SECRET_KEY in your .env file. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ---------------------------------------------------------------------------
# Password hashing — bcrypt via passlib, with SHA-256 legacy support
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Regex to detect old SHA-256 hex hashes (exactly 64 hex chars)
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Supports both:
    - bcrypt hashes (new — starts with $2b$)
    - SHA-256 hex hashes (legacy — 64 hex chars, unsalted)

    Legacy SHA-256 verification allows transparent migration: on successful
    login the caller should re-hash with ``get_password_hash`` and persist.
    """
    if _SHA256_HEX_RE.match(hashed_password):
        # Legacy SHA-256 fallback
        import hashlib
        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == hashed_password
    return pwd_context.verify(plain_password, hashed_password)

def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    return _create_token(
        subject,
        "access",
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    return _create_token(
        subject,
        "refresh",
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_invite_token(subject: str) -> str:
    return _create_token(subject, "invite", timedelta(hours=72))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Returns True if the stored hash should be upgraded.

    This covers:
    - Old SHA-256 hex hashes (always need rehash)
    - bcrypt hashes that use a deprecated cost factor
    """
    if _SHA256_HEX_RE.match(hashed_password):
        return True
    return pwd_context.needs_update(hashed_password)



# ---------------------------------------------------------------------------
# JWT token decoding
# ---------------------------------------------------------------------------
def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
