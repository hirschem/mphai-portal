import pytest
from app.models.config import get_settings

def test_api_write_failure_returns_standard_error_shape(monkeypatch, client):
    settings = get_settings()
    # Patch atomic_write_bytes to always fail
    async def fail_write(*args, **kwargs):
        raise IOError("disk full")
    monkeypatch.setattr("app.storage.file_manager.atomic_write_bytes", fail_write)
    # Use demo password for auth
    headers = {"Authorization": f"Bearer {settings.demo_password}"}
    files = {"file": ("fail.png", b"data", "image/png")}
    response = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert response.status_code >= 400
    data = response.json()
    assert "error" in data
    err = data["error"]
    assert all(k in err for k in ("code", "message", "request_id"))
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]
