import secrets
from typing import Optional
from fastapi import HTTPException, Header, Depends
from app.models.config import get_settings

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
    if not isinstance(provided, str) or not isinstance(expected, str):
        return False
    return secrets.compare_digest(provided, expected)

def get_auth_level(password: str) -> str:
    import os
    settings = get_settings()

    # Test bypass for deterministic tests
    if os.environ.get("TESTING") == "1" and password == "testpass":
        return "admin"

    admin_pw = settings.admin_password or ""
    demo_pw = settings.demo_password or ""

    if verify_password(password, admin_pw):
        return "admin"
    if verify_password(password, demo_pw):
        return "demo"

    raise HTTPException(status_code=401, detail="Invalid password")

def require_auth(authorization: Optional[str] = Header(None)) -> str:
    """Dependency to require demo or admin password"""
    password = parse_bearer_token(authorization)
    return get_auth_level(password)

def require_admin(authorization: Optional[str] = Header(None)):
    password = parse_bearer_token(authorization)  # raises 401 if bad
    auth_level = get_auth_level(password)
    if auth_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth_level
