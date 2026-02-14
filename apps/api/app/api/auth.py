
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_auth_level
from app.security.rate_limit import RateLimiter
from fastapi import Request, HTTPException

router = APIRouter()

class LoginRequest(BaseModel):
    password: str


rate_limiter = RateLimiter()

@router.post("/login")
async def login(request: LoginRequest, req: Request):
    # Rate limit by client IP (TRUST_PROXY_HEADERS/X-Forwarded-For)
    trust_proxy = getattr(req.app.state, "TRUST_PROXY_HEADERS", True)
    if trust_proxy:
        xff = req.headers.get("x-forwarded-for")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = req.client.host if req.client else "unknown"
    else:
        ip = req.client.host if req.client else "unknown"
    rate_limiter.check(ip, "login", 5)

    # Minimal debug output
    from app.models.config import get_settings
    admin_pw = get_settings().admin_password
    print(f"[DEBUG] Received password length: {len(request.password)}")
    print(f"[DEBUG] ADMIN_PASSWORD loaded: {bool(admin_pw)}")
    try:
        level = get_auth_level(request.password)
        print(f"[DEBUG] Comparison passes: {level == 'admin'}")
    except Exception as e:
        print(f"[DEBUG] Comparison error: {e}")
        raise
    return {"level": level}

