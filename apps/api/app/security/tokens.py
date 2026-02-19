import os
import base64
import hmac
import hashlib
import time

def create_access_token(data: dict, expires_in: int = 3600) -> str:
    """Minimal, insecure (non-JWT) token for demo/admin login. Not for production secrets!"""
    secret = os.environ.get("ADMIN_PASSWORD", "demo2026")  # Use a real secret in production
    payload = f"{data['level']}:{int(time.time()) + expires_in}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(payload.encode() + b"." + sig).decode()
    return token
