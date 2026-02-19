def test_login_returns_access_token(client, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "demo2026")
    r = client.post("/api/auth/login", json={"password": "demo2026"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data and isinstance(data["access_token"], str) and len(data["access_token"]) > 20
    assert data.get("token_type") == "bearer"
    assert data.get("level") == "demo"

def test_generate_accepts_bearer_token(client, monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "demo2026")
    login = client.post("/api/auth/login", json={"password": "demo2026"}).json()
    token = login["access_token"]
    r = client.post(
        "/api/proposals/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_id": "t1", "raw_text": "hello", "document_type": "proposal"},
    )
    assert r.status_code != 401
