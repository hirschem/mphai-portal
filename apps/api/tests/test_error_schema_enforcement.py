from app.main import create_app
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse
from fastapi import APIRouter



# Register the test routes at module scope so they are always available

_test_router = APIRouter()

async def direct_json_error():
    return JSONResponse({"detail": "Invalid password"}, status_code=401)

@_test_router.get("/test-direct-json-error-raw")
async def direct_json_error_raw():
    return JSONResponse({"detail": "Invalid password", "__marker": "raw"}, status_code=401)


test_app = create_app()

# --- Build a fresh app for testing, register test routes, then wrap if needed ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse
from fastapi import APIRouter
from app.middleware.error_handlers import add_global_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.enforce_request_id_json_errors import EnforceRequestIDInJSONErrorsMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.models.config import get_settings
from app.api import transcribe, proposals, history, auth, books

def build_test_app() -> FastAPI:
    app = FastAPI(
        title="MPH Handwriting API",
        description="Transcribe handwritten proposals to professional documents",
        version="0.1.0"
    )
    add_global_error_handlers(app)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(EnforceRequestIDInJSONErrorsMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    settings = get_settings()

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

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(transcribe.router, prefix="/api/transcribe", tags=["transcribe"])
    app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
    app.include_router(history.router, prefix="/api/history", tags=["history"])
    app.include_router(books.router, prefix="/api/book", tags=["book"])

    @app.get("/")
    async def root():
        return {
            "message": "MPH Handwriting API",
            "docs": "/docs"
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app

# Register the test routes at module scope so they are always available
_test_router = APIRouter()

@_test_router.get("/test-direct-json-error")
async def direct_json_error():
    return JSONResponse({"detail": "Invalid password"}, status_code=401)

@_test_router.get("/test-direct-json-error-raw")
async def direct_json_error_raw():
    return JSONResponse({"detail": "Invalid password", "__marker": "raw"}, status_code=401)

# Build the app, register test routes, then wrap if needed
base_app = build_test_app()
base_app.include_router(_test_router)
settings = get_settings()
if settings.ENFORCE_REQUEST_SIZE_LIMIT:
    app = RequestSizeLimitMiddleware(
        base_app,
        max_bytes=settings.MAX_REQUEST_BYTES,
    )
else:
    app = base_app
client = TestClient(app)

def test_json_error_schema_401():
    import os
    os.environ["ERROR_SCHEMA_DEBUG"] = "1"
    resp = client.get("/test-direct-json-error")
    assert resp.status_code == 401
    assert resp.headers.get("x-request-id")
    data = resp.json()
    assert data["request_id"] == resp.headers["x-request-id"]
    assert data["error_code"] == "UNAUTHORIZED"
    assert data["message"] == "Invalid password"
    assert "detail" in data  # original field preserved

    # Also check the raw route
    resp_raw = client.get("/test-direct-json-error-raw")
    data_raw = resp_raw.json()
    assert data_raw["detail"] == "Invalid password"
    assert data_raw.get("__marker") == "raw"

def test_json_error_schema_404():
    resp = client.get("/this-path-does-not-exist-xyz")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error_code"] == "NOT_FOUND"
    assert isinstance(data["message"], str)
    assert data["request_id"] == resp.headers["x-request-id"]
