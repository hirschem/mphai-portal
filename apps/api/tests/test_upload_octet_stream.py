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

def test_octet_stream_heic_allowed(tmp_path):
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    token = login_token()
    files = [
        ("file", ("photo1.heic", io.BytesIO(make_image_bytes("img1")), "application/octet-stream")),
        ("file", ("photo2.HEIC", io.BytesIO(make_image_bytes("img2")), "application/octet-stream")),
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert resp.status_code == 200, resp.text
    raw_text = resp.json()["raw_text"]
    assert "--- Page 1 ---" in raw_text and "--- Page 2 ---" in raw_text

def test_octet_stream_pdf_rejected(tmp_path):
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    token = login_token()
    files = [
        ("file", ("doc1.pdf", io.BytesIO(b"%PDF-1.4"), "application/octet-stream")),
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert resp.status_code == 400, resp.text
    data = resp.json()
    assert data["error_code"] == "invalid_file"
    assert "image" in data["message"].lower()
