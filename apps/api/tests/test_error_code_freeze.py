
import pytest
import json
import importlib
from app.main import create_app
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from app.middleware.error_handlers import error_response

# Register the test routes at module scope so they are always available
_test_router = APIRouter()
@_test_router.get("/test-direct-json-error")
async def direct_json_error(request: Request):
    request_id = getattr(request.state, "request_id", None)
    return error_response("UNAUTHORIZED", "Invalid password", request_id, 401)

@_test_router.get("/test-direct-json-error-raw")
async def direct_json_error_raw():
    return JSONResponse({"detail": "Invalid password", "__marker": "raw"}, status_code=401)

# Create the app and include test routes
app = create_app()
app.include_router(_test_router)

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
    from app.models.config import get_settings
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
