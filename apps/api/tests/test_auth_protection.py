

from app.models.config import get_settings
settings = get_settings()

import pytest
from unittest.mock import AsyncMock

def test_protected_requires_auth(monkeypatch, client):
    from app.api import transcribe as transcribe_api
    class FakeOCRService:
        async def transcribe_image(self, *a, **kw):
            return "OCR_TEXT_STUB"
    def fake_get_ocr_service():
        return FakeOCRService()
    monkeypatch.setattr(transcribe_api, "get_ocr_service", fake_get_ocr_service)
    # Ensure no Authorization header is sent
    resp = client.post(
        "/api/transcribe/upload",
        headers={},
        files={"file": ("test.png", b"1234", "image/png")},
    )
    assert resp.status_code == 401

def test_protected_accepts_demo(monkeypatch, client):
    from app.api import transcribe as transcribe_api
    from unittest.mock import AsyncMock
    demo_pw = settings.demo_password
    class FakeOCRService:
        async def transcribe_image(self, *a, **kw):
            return "OCR_TEXT_STUB"
    def fake_get_ocr_service():
        return FakeOCRService()
    monkeypatch.setattr(transcribe_api, "get_ocr_service", fake_get_ocr_service)
    # Patch awaited functions with AsyncMock
    monkeypatch.setattr(transcribe_api.file_manager, "save_upload", AsyncMock(return_value="/tmp/fake.png"))
    resp = client.post(
        "/api/transcribe/upload",
        headers={"Authorization": f"Bearer {demo_pw}"},
        files={"file": ("test.png", b"1234", "image/png")}
    )
    assert resp.status_code != 401

def test_invalid_authorization_header_format_returns_401(monkeypatch, client):
    from app.api import transcribe as transcribe_api
    class FakeOCRService:
        async def transcribe_image(self, *a, **kw):
            return "OCR_TEXT_STUB"
    def fake_get_ocr_service():
        return FakeOCRService()
    monkeypatch.setattr(transcribe_api, "get_ocr_service", fake_get_ocr_service)
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
def test_malformed_authorization_headers_return_401(monkeypatch, client, header_value):
    # Use GET /api/proposals/download/testid (protected, minimal work before auth)
    import app.api.proposals as proposals_mod
    # Patch file_manager and export_service to raise if called (should not be called)
    monkeypatch.setattr(proposals_mod.file_manager, "load_proposal", lambda *a, **kw: pytest.fail("Should not hit storage on malformed auth"))
    monkeypatch.setattr(proposals_mod.export_service, "export_document", lambda *a, **kw: pytest.fail("Should not hit export on malformed auth"))
    resp = client.get("/api/proposals/download/testid", headers={"Authorization": header_value})
    assert resp.status_code == 401

def test_admin_only_still_enforced(client):
    demo_pw = settings.demo_password
    admin_pw = settings.admin_password
    # /api/history/list is admin only
    resp = client.get("/api/history/list", headers={"Authorization": f"Bearer {demo_pw}"})
    assert resp.status_code == 403
    resp = client.get("/api/history/list", headers={"Authorization": f"Bearer {admin_pw}"})
    # Accept any non-401/403 (could be 200, 404, 422, etc.)
    assert resp.status_code not in (401, 403)
