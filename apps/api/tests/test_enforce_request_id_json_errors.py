import pytest
from fastapi.testclient import TestClient
from app.main import fastapi_app, app
from starlette.responses import JSONResponse
from fastapi import APIRouter

# Register the test route at module scope so it is always available
router = APIRouter()
from app.middleware.error_handlers import error_response
@router.get("/test-direct-json-error")
async def direct_json_error(request):
    request_id = getattr(request.state, "request_id", None)
    return error_response("UNAUTHORIZED", "fail", request_id, 401)
fastapi_app.include_router(router)

client = TestClient(app)

def test_json_error_response_includes_request_id():
    resp = client.get("/test-direct-json-error")
    assert resp.status_code == 401
    assert resp.headers.get("x-request-id")
    data = resp.json()
    assert "request_id" in data
    assert data["request_id"] == resp.headers["x-request-id"]
