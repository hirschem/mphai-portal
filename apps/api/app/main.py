import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import transcribe, proposals, history, auth, books
from app.middleware.error_handlers import add_global_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.models.config import get_settings
from app.middleware.request_size_limit import RequestSizeLimitMiddleware

DEPLOY_FINGERPRINT = "cors-v2-20260216-1849"

# --- Redact Authorization header in logs (minimal filter) ---
class RedactAuthFilter(logging.Filter):
    def filter(self, record):
        # Redact Authorization in args dict
        if hasattr(record, 'args') and isinstance(record.args, dict):
            args = dict(record.args)
            if 'authorization' in args:
                args['authorization'] = '[REDACTED]'
            record.args = args
        # Redact Authorization in msg string
        if hasattr(record, 'msg') and isinstance(record.msg, str) and 'authorization' in record.msg.lower():
            record.msg = record.msg.replace('Authorization', 'Authorization[REDACTED]')
        return True

for handler in logging.getLogger().handlers:
    handler.addFilter(RedactAuthFilter())

def create_app(settings_override=None, auth_public_paths=None, auth_public_prefixes=None) -> FastAPI:
    """
    Factory for FastAPI app. Accepts test overrides:
      - settings_override: custom settings object (for test isolation)
      - auth_public_paths: set of exact paths to bypass auth (test-only)
      - auth_public_prefixes: tuple/list of prefixes to bypass auth (test-only)
    """

    import os
    logger = logging.getLogger(__name__)

    app = FastAPI(
        title="MPH Handwriting API",
        description="Transcribe handwritten proposals to professional documents",
        version="0.1.0"
    )

    demo_pw = os.getenv("DEMO_PASSWORD")
    print(f"=== STARTUP demo_password_configured={bool(demo_pw)} ===")

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    add_global_error_handlers(app)
    # PHASE 1: Universal error contract for all exceptions
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from fastapi import HTTPException
    import uuid
    # from fastapi.responses import JSONResponse  # Removed: unused import
    from app.middleware.error_handlers import error_response

    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
        # Compose a single string message from all validation errors
        message = "; ".join([f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in exc.errors()])
        return error_response("VALIDATION_ERROR", message, request_id, 422)

    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
        code = "HTTP_ERROR"
        if exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        return error_response(code, str(exc.detail), request_id, exc.status_code)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(HTTPException, starlette_http_exception_handler)

    # Register request ID middleware
    app.add_middleware(RequestIDMiddleware)
    # Register AuthGate as function-based middleware (replaces class-based AuthGateMiddleware)
    DEFAULT_PUBLIC_PREFIXES = (
        "/api/auth",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
    )
    from starlette.routing import Match

    # Allow test to override settings (for rate limiter, etc.)
    if settings_override is not None:
        def get_settings_override():
            return settings_override
        import app.models.config as config_mod
        config_mod.get_settings = get_settings_override

    # AuthGate config
    _public_paths = set(auth_public_paths) if auth_public_paths else set()
    _public_prefixes = tuple(auth_public_prefixes) if auth_public_prefixes else DEFAULT_PUBLIC_PREFIXES

    @app.middleware("http")
    async def auth_gate(request: Request, call_next):
        path = request.url.path
        method = request.method

        # --- Allow OPTIONS through auth gate ---
        if method == "OPTIONS":
            return await call_next(request)

        # Public paths or prefixes
        bypass = (path in _public_paths) or any(path.startswith(p) for p in _public_prefixes)
        if bypass:
            response = await call_next(request)
            response.headers["x-auth-bypass"] = "1"
            return response

        # Don’t mask 404s: only enforce auth if a route exists for this path
        scope = request.scope
        route_exists = False
        for r in request.app.router.routes:
            match, _ = r.matches(scope)
            if match in (Match.FULL, Match.PARTIAL):
                route_exists = True
                break

        if not route_exists:
            return await call_next(request)

        # Enforce Bearer token
        auth = (request.headers.get("authorization") or "").strip()
        if not auth.startswith("Bearer "):
            rid = getattr(request.state, "request_id", None)
            return error_response("UNAUTHORIZED", "Missing or invalid authorization token", rid, 401)

        token = auth[len("Bearer "):].strip()
        if not token:
            rid = getattr(request.state, "request_id", None)
            return error_response("UNAUTHORIZED", "Missing or invalid authorization token", rid, 401)

        return await call_next(request)

    # Register request size limit middleware
    app.add_middleware(RequestSizeLimitMiddleware)
    # Other middleware
    # app.add_middleware(EnforceRequestIDInJSONErrorsMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # --- CORS Stabilization: Add CORSMiddleware LAST (outermost) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://mphai.app",
            "https://www.mphai.app",
        ],
        allow_origin_regex=r"^https://([a-z0-9-]+\.)*vercel\.app$",
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=86400,
    )

    # Register routes
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(transcribe.router, prefix="/api/transcribe", tags=["transcribe"])
    app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
    app.include_router(history.router, prefix="/api/history", tags=["history"])
    app.include_router(books.router, prefix="/api/book", tags=["book"])
    from app.api import admin_saves
    app.include_router(admin_saves.router, tags=["admin-saves"])

    # Register RateLimitException handler for correct error shaping
    from app.security.rate_limit import RateLimitException
    from app.middleware.error_handlers import error_response
    @app.exception_handler(RateLimitException)
    async def ratelimit_exception_handler(request: Request, exc: RateLimitException):
        request_id = getattr(request.state, "request_id", None)
        return error_response(
            "RATE_LIMITED",
            str(exc),
            request_id,
            429,
            include_detail=True,
            detail_error="Too many requests",
        )

    return app

# Uvicorn entrypoint
# --- Exported app instance for runtime and tests ---
app = create_app()
fastapi_app = app