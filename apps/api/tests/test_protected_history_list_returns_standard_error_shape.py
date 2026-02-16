import pytest

def test_protected_history_list_returns_standard_error_shape(client):
    resp = client.get("/api/history/list")
    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data
    err = data["error"]
    assert "request_id" in err
    assert resp.headers["X-Request-ID"]
    assert resp.headers["X-Request-ID"] == err["request_id"]
    assert "detail" not in data
