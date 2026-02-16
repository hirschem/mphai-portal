import logging
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import APIRouter, Request
from fastapi import FastAPI

import logging
from starlette.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import APIRouter, Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transcribe, proposals, history, auth, books
from app.middleware.error_handlers import add_global_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.enforce_request_id_json_errors import EnforceRequestIDInJSONErrorsMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.models.config import get_settings

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

def create_app() -> FastAPI:
    app = FastAPI(
        title="MPH Handwriting API",
        description="Transcribe handwritten proposals to professional documents",
        version="0.1.0"
    )

    add_global_error_handlers(app)
    # PHASE 1: Universal error contract for all exceptions
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from fastapi import HTTPException
    import uuid
    from fastapi.responses import JSONResponse
    from app.middleware.error_handlers import error_response
    from fastapi import Request

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

    # Register request ID middleware first
    app.add_middleware(RequestIDMiddleware)
    # Register AuthGate as function-based middleware (replaces class-based AuthGateMiddleware)
    PUBLIC_PREFIXES = (
        "/api/auth",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
    )
    from fastapi import Request
    from app.middleware.error_handlers import error_response
    from starlette.routing import Match
    from fastapi import Request
    from app.middleware.error_handlers import error_response

    PUBLIC_PREFIXES = (
        "/api/auth",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
    )

    @app.middleware("http")
    async def auth_gate(request: Request, call_next):
        path = request.url.path
        method = request.method

        if method == "OPTIONS":
            return await call_next(request)

        # Public paths only
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

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
    # Register request size limit middleware next
    from app.middleware.request_size_limit import RequestSizeLimitMiddleware
    app.add_middleware(RequestSizeLimitMiddleware)
    # Other middleware
    # app.add_middleware(EnforceRequestIDInJSONErrorsMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # CORS middleware for Next.js frontend (must be last/outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings = get_settings()

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
    from fastapi import Request
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

# Compatibility alias: some tests import fastapi_app
fastapi_app = app
fastapi_app = app


