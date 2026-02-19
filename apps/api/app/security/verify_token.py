import os
import base64
import hmac
import hashlib
import time
from fastapi import HTTPException

def verify_access_token(token: str) -> str:
    """Verify minimal access_token and return level if valid, else raise HTTPException(401)"""
    secret = os.environ.get("ADMIN_PASSWORD", "demo2026")
    try:
        decoded = base64.urlsafe_b64decode(token.encode())
        payload, sig = decoded.rsplit(b".", 1)
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected_sig):
            raise ValueError("Invalid signature")
        level, exp = payload.decode().split(":")
        if int(exp) < int(time.time()):
            raise ValueError("Token expired")
        if level not in ("admin", "demo"):
            raise ValueError("Invalid level")
        return level
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
