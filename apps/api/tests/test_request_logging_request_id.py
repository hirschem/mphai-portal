import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_request_logging_sets_logrecord_request_id(caplog):
    caplog.set_level("INFO")
    client = TestClient(app)
    r = client.get("/health", headers={"X-Request-Id": "rid-test-123"})
    assert r.status_code == 200
    records = [rec for rec in caplog.records if hasattr(rec, "request_id")]
    assert records, "Expected request logging records"
    assert any(rec.request_id == "rid-test-123" for rec in records), \
        "LogRecord.request_id must be populated (not just JSON message)"
