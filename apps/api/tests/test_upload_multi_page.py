import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def make_image_bytes(text: str) -> bytes:
    return f"PNGDATA-{text}".encode()

def login_token():
    resp = client.post("/api/auth/login", json={"password": "demo2026"})
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_upload_four_pages(tmp_path):
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    token = login_token()
    files = [
        ("files", (f"page{i+1}.png", io.BytesIO(make_image_bytes(f"page{i+1}")), "image/png"))
        for i in range(4)
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert resp.status_code == 200, resp.text
    raw_text = resp.json()["raw_text"]
    for i in range(1, 5):
        assert f"--- Page {i} ---" in raw_text
    assert raw_text.index("--- Page 1 ---") < raw_text.index("--- Page 2 ---") < raw_text.index("--- Page 3 ---") < raw_text.index("--- Page 4 ---")

def test_upload_ten_pages(tmp_path):
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    token = login_token()
    files = [
        ("files", (f"page{i+1}.png", io.BytesIO(make_image_bytes(f"page{i+1}")), "image/png"))
        for i in range(10)
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert resp.status_code == 200, resp.text
    raw_text = resp.json()["raw_text"]
    for i in range(1, 11):
        assert f"--- Page {i} ---" in raw_text
    assert raw_text.index("--- Page 1 ---") < raw_text.index("--- Page 10 ---")

def test_upload_exceeds_max_pages(tmp_path):
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    app_config.get_settings().MAX_UPLOAD_PAGES = 5
    token = login_token()
    files = [
        ("files", (f"page{i+1}.png", io.BytesIO(make_image_bytes(f"page{i+1}")), "image/png"))
        for i in range(6)
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert resp.status_code == 422, resp.text
    assert resp.json()["error_code"] == "VALIDATION_ERROR"
    assert "Too many pages" in resp.json()["message"]
