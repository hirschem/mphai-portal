import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def make_image_bytes(text: str) -> bytes:
    return f"PNGDATA-{text}".encode()

def test_upload_two_files_repeated_file_field(tmp_path):
    from app.models import config as app_config
    app_config.get_settings().MAX_REQUEST_BYTES = 1000000
    token = client.post("/api/auth/login", json={"password": "demo2026"}).json()["access_token"]
    files = [
        ("file", ("page1.png", io.BytesIO(make_image_bytes("Alpha")), "image/png")),
        ("file", ("page2.png", io.BytesIO(make_image_bytes("Bravo")), "image/png")),
    ]
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/transcribe/upload", files=files, headers=headers)
    assert resp.status_code == 200, resp.text
    raw_text = resp.json()["raw_text"]
    assert "--- Page 1 ---" in raw_text
    assert "--- Page 2 ---" in raw_text
    assert raw_text.index("--- Page 1 ---") < raw_text.index("--- Page 2 ---")
    # Accept stub text, just check both markers present
