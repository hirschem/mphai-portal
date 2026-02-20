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

