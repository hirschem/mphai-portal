import logging
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
    # Add request ID and logging middleware first
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(EnforceRequestIDInJSONErrorsMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    settings = get_settings()

    # CORS middleware for Next.js frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "https://mphai.app",
            "https://www.mphai.app"
        ],
        allow_origin_regex=r"^https://.*\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(transcribe.router, prefix="/api/transcribe", tags=["transcribe"])
    app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
    app.include_router(history.router, prefix="/api/history", tags=["history"])
    app.include_router(books.router, prefix="/api/book", tags=["book"])
    from app.api import admin_saves
    app.include_router(admin_saves.router)

    @app.get("/")
    async def root():
        return {
            "message": "MPH Handwriting API",
            "docs": "/docs"
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Wrap with pure ASGI middleware last, so all entrypoints use the wrapped app
    if settings.ENFORCE_REQUEST_SIZE_LIMIT:
        return RequestSizeLimitMiddleware(
            app,
            max_bytes=settings.MAX_REQUEST_BYTES,
        )
    else:
        return app

# Exports for production
fastapi_app = create_app()  # This is the fully constructed app (with or without wrapper)
app = fastapi_app
from app.middleware.error_handlers import add_global_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.enforce_request_id_json_errors import EnforceRequestIDInJSONErrorsMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
import logging
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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transcribe, proposals, history, auth, books


from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.models.config import get_settings




fastapi_app = FastAPI(
    title="MPH Handwriting API",
    description="Transcribe handwritten proposals to professional documents",
    version="0.1.0"
)
add_global_error_handlers(fastapi_app)

# Add request ID and logging middleware first
fastapi_app.add_middleware(RequestIDMiddleware)
fastapi_app.add_middleware(EnforceRequestIDInJSONErrorsMiddleware)
fastapi_app.add_middleware(RequestLoggingMiddleware)

settings = get_settings()

# CORS middleware for Next.js frontend
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://mphai.app",
        "https://www.mphai.app"
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
fastapi_app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
fastapi_app.include_router(transcribe.router, prefix="/api/transcribe", tags=["transcribe"])
fastapi_app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
fastapi_app.include_router(history.router, prefix="/api/history", tags=["history"])
fastapi_app.include_router(books.router, prefix="/api/book", tags=["book"])

@fastapi_app.get("/")
async def root():
    return {
        "message": "MPH Handwriting API",
        "docs": "/docs"
    }

@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}

# Wrap with pure ASGI middleware last, so all entrypoints use the wrapped app
if settings.ENFORCE_REQUEST_SIZE_LIMIT:
    app = RequestSizeLimitMiddleware(
        fastapi_app,
        max_bytes=settings.MAX_REQUEST_BYTES,
    )
else:
    app = fastapi_app


