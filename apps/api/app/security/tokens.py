def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode())
import os
import base64
import hmac
import hashlib
import time

def create_access_token(data: dict, expires_in: int = 3600) -> str:
    """Minimal, insecure (non-JWT) token for demo/admin login. Not for production secrets!"""
    secret = os.environ.get("ADMIN_PASSWORD", "demo2026")  # Use a real secret in production
    payload = f"{data['level']}:{int(time.time()) + expires_in}".encode()
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return f"{_b64u_encode(payload)}.{_b64u_encode(sig)}"
