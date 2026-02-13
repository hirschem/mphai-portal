import secrets
from typing import Optional
from fastapi import HTTPException, Header, Depends
from app.models.config import get_settings

settings = get_settings()

def parse_bearer_token(authorization: Optional[str]) -> str:
    """Strict Bearer token parser (case-insensitive, no extra parts, no empty token)"""
    if not authorization or not isinstance(authorization, str):
        raise HTTPException(status_code=401, detail="Unauthorized")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Unauthorized")
    return parts[1]

def verify_password(provided: str, expected: str) -> bool:
    """Constant-time password check"""
    return secrets.compare_digest(provided, expected)

def get_auth_level(password: str) -> str:
    if verify_password(password, settings.admin_password):
        return "admin"
    elif verify_password(password, settings.demo_password):
        return "demo"
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

def require_auth(authorization: Optional[str] = Header(None)) -> str:
    """Dependency to require demo or admin password"""
    password = parse_bearer_token(authorization)
    return get_auth_level(password)

def require_admin(authorization: Optional[str] = Header(None)):
    """Dependency to require admin password"""
    try:
        password = parse_bearer_token(authorization)
    except HTTPException as e:
        # Missing/malformed header: 401
        raise
    auth_level = get_auth_level(password)
    if auth_level != "admin":
        # Valid token, but not admin: 403
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth_level
