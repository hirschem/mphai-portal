from __future__ import annotations

import json
from typing import Callable, Optional
import uuid

from app.models.config import get_settings
from app.middleware.error_handlers import error_response

def _get_content_length(headers) -> int | None:
    for k, v in headers or []:
        if k.lower() == b"content-length":
            try:
                return int(v.decode("ascii"))
            except Exception:
                return None
    return None

class RequestSizeLimitMiddleware:
    def __init__(self, app: Callable, **_):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        settings = get_settings()
        if not getattr(settings, "ENFORCE_REQUEST_SIZE_LIMIT", False):
            return await self.app(scope, receive, send)

        max_bytes = int(getattr(settings, "MAX_REQUEST_BYTES", 25_000_000))

        headers = scope.get("headers") or []
        content_length = _get_content_length(headers)
        # (guarded block for content_length > max_bytes is below)
        if content_length is not None and content_length > max_bytes:
            request_id = str(uuid.uuid4())
            resp = error_response(
                "PAYLOAD_TOO_LARGE",
                f"Request body too large. Max allowed is {max_bytes} bytes.",
                request_id,
                413,
            )
            body = resp.body
            out_headers = [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"x-request-id", request_id.encode("ascii")),
            ]
            await send({"type": "http.response.start", "status": 413, "headers": out_headers})
            await send({"type": "http.response.body", "body": body, "more_body": False})
            return

        # stream guard (same as before)
        buffered = []
        seen = 0
        while True:
            message = await receive()
            if message["type"] != "http.request":
                buffered.append(message)
                break
            chunk = message.get("body", b"") or b""
            seen += len(chunk)
            buffered.append(message)
            # (guarded block for seen > max_bytes is below)
            if seen > max_bytes:
                request_id = str(uuid.uuid4())
                resp = error_response(
                    "PAYLOAD_TOO_LARGE",
                    f"Request body too large. Max allowed is {max_bytes} bytes.",
                    request_id,
                    413,
                )
                body = resp.body
                out_headers = [
                    (b"content-type", b"application/json; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"x-request-id", request_id.encode("ascii")),
                ]
                await send({"type": "http.response.start", "status": 413, "headers": out_headers})
                await send({"type": "http.response.body", "body": body, "more_body": False})
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

        return await self.app(scope, replay_receive, send)


