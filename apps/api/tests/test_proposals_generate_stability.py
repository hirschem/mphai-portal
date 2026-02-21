from app.services.openai_guard import OpenAIFailure
def test_generate_openai_failure(monkeypatch):
    from app.api import proposals as proposals_api
    def fake_get_formatting_service():
        class FakeFormattingService:
            async def rewrite_professional(self, *args, **kwargs):
                raise OpenAIFailure(code="OPENAI_TIMEOUT", message="timeout", attempts=3)
            async def structure_proposal(self, *args, **kwargs):
                return {}
        return FakeFormattingService()
    monkeypatch.setattr(proposals_api, "get_formatting_service", fake_get_formatting_service, raising=True)
    client = TestClient(app)
    payload = {"session_id": "fail1", "raw_text": "x", "document_type": "proposal"}
    headers = {"Authorization": "Bearer testpass", "X-Request-ID": "test-rid-123"}
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code == 503
    data = resp.json()
    assert data["error"]["code"] == "OPENAI_TIMEOUT"
    assert data["request_id"] == "test-rid-123"
    assert resp.headers.get("x-request-id") == "test-rid-123"
    msg = data.get("message") or data.get("error", {}).get("message", "")
    assert "temporarily unavailable" in msg
def test_generate_schema_invalid(monkeypatch):
    from app.api import proposals as proposals_api
    def fake_get_formatting_service():
        class FakeFormattingService:
            async def rewrite_professional(self, *args, **kwargs):
                return "ok"
            async def structure_proposal(self, *args, **kwargs):
                return {"total": "not-a-float"}
        return FakeFormattingService()
    monkeypatch.setattr(proposals_api, "get_formatting_service", fake_get_formatting_service, raising=True)
    client = TestClient(app)
    payload = {"session_id": "fail2", "raw_text": "x", "document_type": "proposal"}
    headers = {"Authorization": "Bearer testpass", "X-Request-ID": "test-rid-456"}
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code == 500
    data = resp.json()
    assert data["error"]["code"] == "PROPOSAL_SCHEMA_INVALID"
    assert data["request_id"] == "test-rid-456"
    assert resp.headers.get("x-request-id") == "test-rid-456"
    msg = data.get("message") or data.get("error", {}).get("message", "")
    assert "invalid" in msg.lower()
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_generate_returns_error_if_openai_not_configured(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Use a valid Bearer token (testpass triggers test bypass)
    client = TestClient(app)
    payload = {"session_id": "t1", "raw_text": "hello", "document_type": "proposal"}
    headers = {"Authorization": "Bearer testpass"}
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "generated"
    assert "STUB" in data["professional_text"]

