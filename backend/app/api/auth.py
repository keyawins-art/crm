from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_invite_token,
    decode_token,
    get_password_hash,
    needs_rehash,
    verify_password,
)
from app.db.database import SessionLocal
from app.models import Role, User, UserStatus
from app.models.audit import AuditLog, AuditAction
from app.models.token_blacklist import BlacklistedToken
from app.schemas.auth import (
    AcceptInviteRequest,
    InviteRequest,
    InviteResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    TokenResponse,
    LogoutRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Rate limiter — will be resolved from app.state at runtime
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _is_token_blacklisted(db: Session, jti: str) -> bool:
    """Check if a token's jti has been revoked."""
    return db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first() is not None


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        jti = payload.get("jti")

        if payload.get("type") != "access" or not user_id:
            raise credentials_exception

        user_uuid = UUID(user_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    if jti and _is_token_blacklisted(db, jti):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


# ---------------------------------------------------------------------------
# POST /auth/login — rate-limited (5/minute per IP)
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email_clean = form_data.username.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not user.is_active or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Transparent password rehash: SHA-256 → bcrypt on successful login
    if needs_rehash(user.password_hash):
        user.password_hash = get_password_hash(form_data.password)
        db.add(user)

    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.VIEWED,
        entity_type="User",
        entity_id=user.id,
        details=f"{user.first_name} logged in",
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


# ---------------------------------------------------------------------------
# POST /auth/refresh — validates blacklist
# ---------------------------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check if the refresh token has been revoked
    jti = token_payload.get("jti")
    if jti and _is_token_blacklisted(db, jti):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    try:
        user_id = UUID(token_payload["sub"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Blacklist the old refresh token (single-use rotation)
    if jti:
        exp = token_payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
        db.add(BlacklistedToken(jti=jti, user_id=user.id, expires_at=expires_at))
        db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


# ---------------------------------------------------------------------------
# POST /auth/logout — blacklists the access + refresh token
# ---------------------------------------------------------------------------
@router.post("/logout")
def logout(
    request: Request,
    payload: Optional[LogoutRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke the current access token.  If a refresh_token is provided in the
    request body, revoke that too.
    """
    # Blacklist the access token
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            tok_payload = decode_token(token)
            jti = tok_payload.get("jti")
            exp = tok_payload.get("exp")
            if jti:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
                existing = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()
                if not existing:
                    db.add(BlacklistedToken(jti=jti, user_id=current_user.id, expires_at=expires_at))
        except JWTError:
            pass  # Token decode failed — already invalid, nothing to blacklist

    # Blacklist the refresh token if provided
    if payload and payload.refresh_token:
        try:
            tok_payload = decode_token(payload.refresh_token)
            jti = tok_payload.get("jti")
            exp = tok_payload.get("exp")
            if jti and tok_payload.get("type") == "refresh" and tok_payload.get("sub") == str(current_user.id):
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
                existing = db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()
                if not existing:
                    db.add(BlacklistedToken(jti=jti, user_id=current_user.id, expires_at=expires_at))
        except JWTError:
            pass

    db.commit()
    return {"message": "Logged out successfully — tokens revoked"}


# ---------------------------------------------------------------------------
# POST /auth/invite — admin-only user creation (replaces /register)
# ---------------------------------------------------------------------------
@router.post("/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def invite_user(
    request: Request,
    payload: InviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invite a new user. Only accessible to users with the Admin
    role. Creates the user with status INVITED and generates an invite token.
    """
    # Check admin role
    if not current_user.role or current_user.role.name not in ("Admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can invite users",
        )

    existing = db.query(User).filter(User.email == str(payload.email).strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate the requested role exists
    role = None
    if payload.role_id:
        role = db.query(Role).filter(Role.id == payload.role_id).first()
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role_id")

    # Create user with INVITED status and a random temp password
    import secrets
    temp_password = secrets.token_urlsafe(32)

    user = User(
        email=str(payload.email).strip().lower(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        password_hash=get_password_hash(temp_password),
        is_active=False,  # Not active until they accept the invite
        role_id=role.id if role else None,
    )
    db.add(user)
    db.flush()

    # Generate an invite token (short-lived, 72 hours)
    invite_token = create_invite_token(str(user.id))

    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CREATED,
        entity_type="User",
        entity_id=user.id,
        details=f"Invited {user.email}",
    )
    db.add(audit)
    db.commit()

    return InviteResponse(
        user_id=user.id,
        email=user.email,
        invite_token=invite_token,
        message=f"User {user.email} invited. Share the invite token to let them set their password.",
    )


# ---------------------------------------------------------------------------
# POST /auth/accept-invite — set password and activate account
# ---------------------------------------------------------------------------
@router.post("/accept-invite", response_model=TokenResponse)
@limiter.limit("5/minute")
def accept_invite(
    request: Request,
    payload: AcceptInviteRequest,
    db: Session = Depends(get_db),
):
    """Accept an invite by setting a password. Returns auth tokens."""
    try:
        token_payload = decode_token(payload.invite_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired invite token")

    if token_payload.get("type") != "invite":
        raise HTTPException(status_code=401, detail="Invalid invite token")

    jti = token_payload.get("jti")
    if not jti or _is_token_blacklisted(db, jti):
        raise HTTPException(status_code=401, detail="Invite already used or revoked")

    user_id = token_payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid invite token")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_active:
        raise HTTPException(status_code=400, detail="Invite already accepted")

    # Enforce minimum password length
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.password_hash = get_password_hash(payload.password)
    user.is_active = True

    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.UPDATED,
        entity_type="User",
        entity_id=user.id,
        details=f"{user.first_name} accepted invite and activated account",
    )
    db.add(audit)
    db.add(
        BlacklistedToken(
            jti=jti,
            user_id=user.id,
            expires_at=datetime.fromtimestamp(
                token_payload["exp"], tz=timezone.utc
            ),
        )
    )
    db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------
@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        status=current_user.status.value if current_user.status else None,
        role=current_user.role.name if current_user.role else None,
    )
