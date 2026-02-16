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
    # Add request ID and logging middleware before CORS
    app.add_middleware(RequestIDMiddleware)
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

    return app

# Uvicorn entrypoint

# --- Exported app instance for runtime and tests ---
app = create_app()

# Compatibility alias: some tests import fastapi_app
fastapi_app = app


