
import pytest
import json
import importlib
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from app.middleware.error_handlers import add_global_error_handlers
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.enforce_request_id_json_errors import EnforceRequestIDInJSONErrorsMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_size_limit import RequestSizeLimitMiddleware
from app.models.config import get_settings
from app.api import transcribe, proposals, history, auth, books

# Duplicate of build_test_app from test_error_schema_enforcement.py
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

# Duplicate of _test_router from test_error_schema_enforcement.py
_test_router = APIRouter()

@_test_router.get("/test-direct-json-error")
async def direct_json_error():
    return JSONResponse({"detail": "Invalid password"}, status_code=401)

@_test_router.get("/test-direct-json-error-raw")
async def direct_json_error_raw():
    return JSONResponse({"detail": "Invalid password", "__marker": "raw"}, status_code=401)

ALLOWED_ERROR_CODES = {
    "UNAUTHORIZED",
    "FORBIDDEN",
    "NOT_FOUND",
    "VALIDATION_ERROR",
    "PAYLOAD_TOO_LARGE",
    "INTERNAL_ERROR",
    "HTTP_ERROR",
}



def test_error_code_401():
    import app.main as app_main
    importlib.reload(app_main)
    from fastapi.testclient import TestClient
    with TestClient(app_main.app) as client:
        # Use a real protected endpoint (same as test_invalid_auth)
        payload = {"raw_text": "test", "session_id": "test-session-401"}
        resp = client.post("/api/proposals/generate", json=payload, headers={})
        assert resp.status_code == 401
        data = resp.json()
        assert "error_code" in data
        assert data["error_code"] in ALLOWED_ERROR_CODES
        assert "request_id" in data
        assert isinstance(data["request_id"], str)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert data["error_code"] == "UNAUTHORIZED"

def test_error_code_404():
    import app.main as app_main
    importlib.reload(app_main)
    from fastapi.testclient import TestClient
    with TestClient(app_main.app) as client:
        resp = client.get("/this-path-does-not-exist-xyz")
        assert resp.status_code == 404
        data = resp.json()
        assert "error_code" in data
        assert data["error_code"] in ALLOWED_ERROR_CODES
        assert "request_id" in data
        assert isinstance(data["request_id"], str)
        assert "message" in data
        assert isinstance(data["message"], str)
        assert data["error_code"] == "NOT_FOUND"


def test_error_code_413(monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BYTES", "100")
    monkeypatch.setenv("ENFORCE_REQUEST_SIZE_LIMIT", "1")
    get_settings.cache_clear()

    import app.main as app_main
    importlib.reload(app_main)
    from fastapi.testclient import TestClient
    payload = {"password": "demo2024", "padding": "x" * 2048}
    body = json.dumps(payload).encode("utf-8")
    with TestClient(app_main.app) as client:
        resp = client.post(
            "/api/auth/login",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 413
        data = resp.json()
        assert data["error_code"] == "PAYLOAD_TOO_LARGE"
        assert isinstance(data.get("message"), str) and "too large" in data["message"].lower()
