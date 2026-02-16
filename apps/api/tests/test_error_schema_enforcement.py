import pytest
from app.main import create_app
from fastapi.testclient import TestClient
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from app.middleware.error_handlers import error_response

# Register the test routes at module scope so they are always available
_test_router = APIRouter()
@_test_router.get("/test-direct-json-error")
async def direct_json_error(request: Request):
    request_id = getattr(request.state, "request_id", None)
    return error_response("UNAUTHORIZED", "Invalid password", request_id, 401, include_detail=True)

@_test_router.get("/test-direct-json-error-raw")
async def direct_json_error_raw():
    return JSONResponse({"detail": "Invalid password", "__marker": "raw"}, status_code=401)

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("ERROR_SCHEMA_DEBUG", "1")
    app = create_app(auth_public_paths={
        "/test-direct-json-error",
        "/test-direct-json-error-raw",
        "/api/test-direct-json-error",
        "/api/test-direct-json-error-raw",
    })
    app.include_router(_test_router)
    return TestClient(app)

def test_middleware_order_contract():
    app = create_app()
    actual = [mw.cls.__name__ for mw in reversed(app.user_middleware)]
    core_expected = [
        "RequestIDMiddleware",
        "BaseHTTPMiddleware",          # AuthGate wrapper
        "RequestSizeLimitMiddleware",
        "RequestLoggingMiddleware",
    ]
    assert actual[:len(core_expected)] == core_expected, (
        "Middleware execution core order changed!\n"
        f"Expected prefix: {core_expected}\nActual:          {actual}"
    )
    tail = actual[len(core_expected):]
    assert tail in ([], ["CORSMiddleware"]), (
        "Unexpected middleware tail!\n"
        f"Expected tail: [] or ['CORSMiddleware']\nActual tail:    {tail}\nFull:           {actual}"
    )
    assert actual.count("BaseHTTPMiddleware") == 1

def test_json_error_schema_401(client):
    resp = client.get("/test-direct-json-error")
    assert resp.status_code == 401
    assert resp.headers.get("x-request-id")
    assert resp.headers.get("x-auth-bypass") == "1"  # Confirm bypass branch hit
    # Optionally print x-auth-path for debugging
    # print("x-auth-path:", resp.headers.get("x-auth-path"))
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

def test_json_error_schema_404(client):
    resp = client.get("/this-path-does-not-exist-xyz")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error_code"] == "NOT_FOUND"
    assert isinstance(data["message"], str)
    assert data["request_id"] == resp.headers["x-request-id"]