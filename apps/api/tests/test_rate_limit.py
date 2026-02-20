import pytest
from fastapi.testclient import TestClient
from app.main import app
import time


import os
os.environ["TESTING"] = "1"
client = TestClient(app)

RATE_LIMIT = 5
GENERATE_LIMIT = 3

def test_login_rate_limit(monkeypatch):
    t = [1000.0]
    monkeypatch.setattr("time.time", lambda: t[0])
    headers = {"X-Forwarded-For": "5.6.7.8"}
    for i in range(RATE_LIMIT):
        resp = client.post("/api/auth/login", json={"password": "testpass"}, headers=headers)
        assert resp.status_code == 200
    resp = client.post("/api/auth/login", json={"password": "testpass"}, headers=headers)
    assert resp.status_code == 429
    assert resp.json()["detail"]["error"]["message"] == "Too many requests: Rate limit exceeded for login"
    # Advance time to next window
    t[0] += 61
    resp = client.post("/api/auth/login", json={"password": "testpass"}, headers=headers)
    assert resp.status_code == 200

def test_generate_rate_limit(monkeypatch):
    t = [2000.0]
    monkeypatch.setattr("time.time", lambda: t[0])
    payload = {
        "session_id": "test-session",
        "raw_text": "test",
        "document_type": "proposal"
    }
    # Provide Authorization header and stable IP for deterministic rate limiting
    headers = {"Authorization": "Bearer testpass", "X-Forwarded-For": "1.2.3.4"}
    # First GENERATE_LIMIT requests should NOT be rate limited (may be 500, just not 429)
    for i in range(GENERATE_LIMIT):
        resp = client.post("/api/proposals/generate", json=payload, headers=headers)
        assert resp.status_code != 429
    # Next request should be rate limited
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code == 429
    data = resp.json()
    assert data["error_code"] == "RATE_LIMITED"
    assert data["message"] == "Rate limit exceeded."
    # After time window reset, should not be rate limited
    t[0] += 61
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code != 429

def test_rate_limit_no_file_write_on_429(monkeypatch, tmp_path):
    t = [3000.0]
    monkeypatch.setattr("time.time", lambda: t[0])
    # Patch file_manager to raise if save_proposal is called on 429
    from app.api.proposals import file_manager
    called = []
    orig_save = file_manager.save_proposal
    def fail_on_call(*a, **kw):
        called.append(True)
        raise AssertionError("Should not write file on 429")
    monkeypatch.setattr(file_manager, "save_proposal", fail_on_call)
    payload = {
        "session_id": "test-session2",
        "raw_text": "test",
        "document_type": "proposal"
    }
    headers = {"Authorization": "Bearer testpass"}
    for i in range(GENERATE_LIMIT):
        resp = client.post("/api/proposals/generate", json=payload, headers=headers)
        assert resp.status_code != 429
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code == 429
    assert not called
import pathlib
import shutil

def snapshot_tree(root):
    """Return set of (relative_path, mtime) for all files/dirs under root."""
    snap = set()
    for p in pathlib.Path(root).rglob("*"):
        snap.add((str(p.relative_to(root)), p.stat().st_mtime))
    return snap

def test_rate_limit_no_file_write_on_429(monkeypatch, tmp_path):
    t = [3000.0]
    monkeypatch.setattr("time.time", lambda: t[0])
    # Set up deterministic client IP and proxy trust
    monkeypatch.setattr("app.api.proposals.rate_limiter._store", {}, raising=False)
    monkeypatch.setattr("app.api.proposals.TRUST_PROXY_HEADERS", True, raising=False)
    payload = {
        "session_id": "test-session2",
        "raw_text": "test",
        "document_type": "proposal"
    }
    headers = {
        "Authorization": "Bearer testpass",
        "X-Forwarded-For": "1.2.3.4"
    }
    # Clean up session dir if exists
    from app.storage.file_manager import FileManager
    fm = FileManager()
    session_dir = fm.sessions_dir / payload["session_id"]
    if session_dir.exists():
        shutil.rmtree(session_dir)
    # Take snapshot before
    snap_before = snapshot_tree(fm.sessions_dir)
    # Hit up to limit
    for i in range(GENERATE_LIMIT):
        resp = client.post("/api/proposals/generate", json=payload, headers=headers)
        assert resp.status_code != 429
    # Take snapshot before 429
    snap_pre429 = snapshot_tree(fm.sessions_dir)
    # 429 request
    resp = client.post("/api/proposals/generate", json=payload, headers=headers)
    assert resp.status_code == 429
    # Take snapshot after 429
    snap_post429 = snapshot_tree(fm.sessions_dir)
    # Assert no new files/dirs created by 429 request
    assert snap_pre429 == snap_post429, f"Filesystem changed on 429: {snap_pre429 ^ snap_post429}"
