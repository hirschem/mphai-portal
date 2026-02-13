import json
import pytest
def load_fixture(name):
    with open(FIXTURE_DIR / name, "r") as f:
        return json.load(f)


import os
import importlib
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

def auth_headers(password="demo2026"):
    return {"Authorization": f"Bearer {password}"}


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "invoices"

@pytest.fixture(autouse=True)
def _reset_env_and_app(monkeypatch):
    monkeypatch.delenv("MAX_REQUEST_BYTES", raising=False)
    monkeypatch.delenv("ENFORCE_REQUEST_SIZE_LIMIT", raising=False)
    from app.models.config import get_settings
    get_settings.cache_clear()
    import app.main as app_main
    importlib.reload(app_main)

@pytest.fixture
def client():
    import app.main as app_main
    with TestClient(app_main.app) as c:
        yield c

def monkeypatch_formatting(monkeypatch):
    from app.api import proposals as proposals_api
    def load_expected(name: str) -> dict:
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    class FakeFormattingService:
        async def rewrite_professional(self, raw_text: str, *args, **kwargs):
            return "PROFESSIONAL_TEXT_STUB"
        async def structure_proposal(self, *args, **kwargs):
            document_type = kwargs.get("document_type")
            if document_type is None and len(args) >= 2 and isinstance(args[1], str):
                document_type = args[1]
            # Return a deep copy to avoid mutation between tests
            import copy
            if document_type == "invoice":
                return copy.deepcopy(load_expected("invoice_expected.json"))
            return copy.deepcopy(load_expected("proposal_expected.json"))

    def fake_get_formatting_service():
        return FakeFormattingService()

    monkeypatch.setattr(proposals_api, "get_formatting_service", fake_get_formatting_service)

def test_generate_proposal(monkeypatch, client):
    monkeypatch_formatting(monkeypatch)
    payload = load_fixture("proposal_input.json")
    resp = client.post("/api/proposals/generate", json=payload, headers=auth_headers())
    print(resp.text)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["document_type"] == "proposal"
    assert "proposal_data" in data
    assert "document_data" in data
    expected = load_fixture("proposal_expected.json")
    for k, v in expected.items():
        assert data["document_data"].get(k) == v

def test_generate_invoice(monkeypatch, client):
    monkeypatch_formatting(monkeypatch)
    payload = load_fixture("invoice_input.json")
    resp = client.post("/api/proposals/generate", json=payload, headers=auth_headers())
    print(resp.text)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["document_type"] == "invoice"
    assert "proposal_data" in data
    assert "document_data" in data
    expected = load_fixture("invoice_expected.json")
    for k, v in expected.items():
        assert data["document_data"].get(k) == v

def test_file_outputs(monkeypatch, tmp_path, client):
    monkeypatch_formatting(monkeypatch)
    payload = load_fixture("invoice_input.json")
    payload["session_id"] = "test-tmp-003"
    resp = client.post("/api/proposals/generate", json=payload, headers=auth_headers())
    print(resp.text)
    assert resp.status_code == 200, resp.text
    from app.storage.file_manager import FileManager
    fm = FileManager()
    session_dir = fm.sessions_dir / payload["session_id"]
    assert (session_dir / "invoice.json").exists()
    assert (session_dir / "invoice.pdf").exists()

def test_missing_required_field(monkeypatch, client):
    monkeypatch_formatting(monkeypatch)
    payload = {"raw_text": "Missing session_id"}
    resp = client.post("/api/proposals/generate", json=payload, headers=auth_headers())
    assert resp.status_code == 422

def test_invalid_auth(monkeypatch, client):
    monkeypatch_formatting(monkeypatch)
    payload = load_fixture("proposal_input.json")
    # Remove auth header
    resp = client.post("/api/proposals/generate", json=payload, headers={})
    assert resp.status_code == 401
