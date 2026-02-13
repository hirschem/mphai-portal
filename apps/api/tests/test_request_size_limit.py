import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.config import get_settings

client = TestClient(app)


def test_rejects_large_content_length(monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BYTES", "100")
    monkeypatch.setenv("ENFORCE_REQUEST_SIZE_LIMIT", "1")
    # Re-instantiate settings to pick up env
    get_settings.cache_clear()
    # Send Content-Length > 100
    headers = {"Content-Length": "150"}
    resp = client.post("/api/auth/login", content=("x" * 150).encode("utf-8"), headers=headers)
    assert resp.status_code == 413
    data = resp.json()
    assert "error_code" in data and data["error_code"] == "PAYLOAD_TOO_LARGE"
    assert "message" in data and "100" in data["message"]


def test_allows_small_request(monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BYTES", "100")
    monkeypatch.setenv("ENFORCE_REQUEST_SIZE_LIMIT", "1")
    get_settings.cache_clear()
    # Send Content-Length < 100
    headers = {"Content-Length": "50"}
    resp = client.post("/api/auth/login", json={"password": "testpass"}, headers=headers)
    # Should pass through to normal handler (200 or 401)
    assert resp.status_code in (200, 401)
    data = resp.json()
    assert "level" in data or "error" in data or "error_code" in data


def test_rejects_large_stream(monkeypatch):
    monkeypatch.setenv("MAX_REQUEST_BYTES", "100")
    monkeypatch.setenv("ENFORCE_REQUEST_SIZE_LIMIT", "1")
    get_settings.cache_clear()
    # No Content-Length, but body > 100 bytes
    resp = client.post("/api/auth/login", content=("x" * 150).encode("utf-8"))
    assert resp.status_code == 413
    data = resp.json()
    assert data["error_code"] == "PAYLOAD_TOO_LARGE"
    assert "100" in data["message"]
