from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.auth import get_auth_level
from app.security.tokens import create_access_token
from app.security.rate_limit import RateLimiter, RateLimitException
from app.middleware.error_handlers import error_response

router = APIRouter()

class LoginRequest(BaseModel):
    password: str

rate_limiter = RateLimiter()

@router.post("/login")
async def login(payload: LoginRequest, req: Request):
    request_id = getattr(req.state, "request_id", None)

    # Rate limit by client IP (TRUST_PROXY_HEADERS/X-Forwarded-For)
    try:
        trust_proxy = getattr(req.app.state, "TRUST_PROXY_HEADERS", True)
        if trust_proxy:
            xff = req.headers.get("x-forwarded-for")
            ip = xff.split(",")[0].strip() if xff else (req.client.host if req.client else "unknown")
        else:
            ip = req.client.host if req.client else "unknown"

        rate_limiter.check(ip, "login", 5)

    except RateLimitException as exc:
        # Must return a response (no exception leak)
        return error_response(
            "RATE_LIMITED",
            str(exc),
            request_id,
            429,
            include_detail=True,
            detail_error="Too many requests",
        )
    except Exception:
        # If limiter itself blows up, still return a response
        return error_response("RATE_LIMIT_ERROR", "Rate limit check failed", request_id, 429)

    # Auth check
    try:
        level = get_auth_level(payload.password)
    except Exception:
        # Any unexpected auth error should still be shaped
        return error_response("UNAUTHORIZED", "Invalid credentials", request_id, 401)

    if level not in ("admin", "demo"):
        return error_response("UNAUTHORIZED", "Invalid credentials", request_id, 401)

    token = create_access_token({"level": level})
    return {"access_token": token, "token_type": "bearer", "level": level}

