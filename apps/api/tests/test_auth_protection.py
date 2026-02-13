
from fastapi.testclient import TestClient
from app.main import app
from app.models.config import get_settings
settings = get_settings()
client = TestClient(app)

import pytest
from unittest.mock import AsyncMock

def test_protected_requires_auth(monkeypatch):
    # Ensure no Authorization header is sent
    resp = client.post(
        "/api/transcribe/upload",
        headers={},
        files={"file": ("test.png", b"1234", "image/png")},
    )
    assert resp.status_code == 401

def test_protected_accepts_demo(monkeypatch):
    from unittest.mock import AsyncMock
    import app.api.transcribe as transcribe_mod
    demo_pw = settings.demo_password
    # Patch awaited functions with AsyncMock
    monkeypatch.setattr("app.api.transcribe.file_manager.save_upload", AsyncMock(return_value="/tmp/fake.png"))
    monkeypatch.setattr("app.api.transcribe.ocr_service.transcribe_image", AsyncMock(return_value="dummy text"))
    resp = client.post(
        "/api/transcribe/upload",
        headers={"Authorization": f"Bearer {demo_pw}"},
        files={"file": ("test.png", b"1234", "image/png")}
    )
    assert resp.status_code != 401

def test_invalid_authorization_header_format_returns_401(monkeypatch):
    # Patch as above to avoid external calls
    import app.api.transcribe as transcribe_mod
    assert hasattr(transcribe_mod.ocr_service, "transcribe_image")
    monkeypatch.setattr(transcribe_mod.ocr_service, "transcribe_image", lambda x: "dummy text")
    files = {'file': ('test.png', b'data', 'image/png')}
    # No 'Bearer ' prefix
    resp = client.post("/api/transcribe/upload", headers={"Authorization": "test123"}, files=files)
    assert resp.status_code == 401

@pytest.mark.parametrize("header_value", [
    "demo-password",
    "Bearer",
    "Bearer   ",
    "Basic abcdef",
    "Bearer a b",
])
def test_malformed_authorization_headers_return_401(monkeypatch, header_value):
    # Use GET /api/proposals/download/testid (protected, minimal work before auth)
    import app.api.proposals as proposals_mod
    # Patch file_manager and export_service to raise if called (should not be called)
    monkeypatch.setattr(proposals_mod.file_manager, "load_proposal", lambda *a, **kw: pytest.fail("Should not hit storage on malformed auth"))
    monkeypatch.setattr(proposals_mod.export_service, "export_document", lambda *a, **kw: pytest.fail("Should not hit export on malformed auth"))
    resp = client.get("/api/proposals/download/testid", headers={"Authorization": header_value})
    assert resp.status_code == 401

def test_admin_only_still_enforced():
    demo_pw = settings.demo_password
    admin_pw = settings.admin_password
    # /api/history/list is admin only
    resp = client.get("/api/history/list", headers={"Authorization": f"Bearer {demo_pw}"})
    assert resp.status_code == 403
    resp = client.get("/api/history/list", headers={"Authorization": f"Bearer {admin_pw}"})
    # Accept any non-401/403 (could be 200, 404, 422, etc.)
    assert resp.status_code not in (401, 403)
