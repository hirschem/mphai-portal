

import json
from typing import Callable, Optional
from app.models.config import get_settings

class RequestSizeLimitMiddleware:
    def __init__(self, app: Callable, **_):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        if not getattr(settings, "ENFORCE_REQUEST_SIZE_LIMIT", False):
            await self.app(scope, receive, send)
            return
        max_bytes = int(getattr(settings, "MAX_REQUEST_BYTES", 25_000_000))

        headers = scope.get("headers") or []
        content_length = _get_content_length(headers)
        if content_length is not None and content_length > max_bytes:
            await _send_413(send, max_bytes)
            return

        buffered = []
        seen = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                buffered.append(message)
                break
            body = message.get("body", b"") or b""
            seen += len(body)
            buffered.append(message)
            if seen > max_bytes:
                await _send_413(send, max_bytes)
                return
            if not message.get("more_body", False):
                break

        i = 0
        async def replay_receive():
            nonlocal i
            if i < len(buffered):
                msg = buffered[i]
                i += 1
                return msg
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, replay_receive, send)

def _get_content_length(headers: list[tuple[bytes, bytes]]) -> Optional[int]:
    for k, v in headers:
        if k.lower() == b"content-length":
            try:
                return int(v.decode("latin-1").strip())
            except (ValueError, UnicodeDecodeError):
                return None
    return None

async def _send_413(send, max_bytes: int) -> None:
    body = json.dumps({
        "error_code": "PAYLOAD_TOO_LARGE",
        "message": f"Request body too large. Max allowed is {max_bytes} bytes."
    }).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body, "more_body": False})
