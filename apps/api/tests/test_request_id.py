import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_request_id_header_echo():
    client = TestClient(app)
    custom_id = "test-req-1234"
    resp = client.get("/api/auth/login", headers={"x-request-id": custom_id})
    assert resp.headers["x-request-id"] == custom_id


def test_request_id_header_generated():
    client = TestClient(app)
    resp = client.get("/api/auth/login")
    assert "x-request-id" in resp.headers
    assert resp.headers["x-request-id"]


def test_request_id_in_error_response():
    client = TestClient(app)
    resp = client.post("/api/auth/login", json={"password": "wrong"})
    data = resp.json()
    assert "request_id" in data
    assert data["request_id"] == resp.headers["x-request-id"]
