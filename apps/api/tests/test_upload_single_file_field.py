import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def make_image_bytes(text: str) -> bytes:
    return f"PNGDATA-{text}".encode()

def test_upload_single_file_field(tmp_path):
    # Patch settings to allow larger uploads for this test
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    # Authenticate using real login endpoint
    login_resp = client.post("/api/auth/login", json={"password": "demo2026"})
    assert login_resp.status_code == 200, login_resp.text
    token = login_resp.json()["access_token"]
    # Send single file with field name 'file'
    file_tuple = ("file", ("page.png", io.BytesIO(make_image_bytes("page1-unique")), "image/png"))
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/transcribe/upload", files=[file_tuple], headers=headers)
    assert response.status_code == 200, response.text
    resp_json = response.json()
    assert "session_id" in resp_json
    assert "raw_text" in resp_json
    raw_text = resp_json["raw_text"]
    assert isinstance(raw_text, str) and len(raw_text) > 0
    assert "--- Page 1 ---" in raw_text
    assert "PROFESSIONAL_TEXT_STUB" in raw_text
