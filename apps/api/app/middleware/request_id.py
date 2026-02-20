from __future__ import annotations
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "x-request-id"

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - If incoming x-request-id exists, reuse it.
    - Otherwise generate UUID4.
    - Store on request.state.request_id
    - Add x-request-id to every response.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import json
        from starlette.responses import JSONResponse
        from starlette.background import BackgroundTask

        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming.strip() if incoming and incoming.strip() else str(uuid.uuid4())
        request.state.request_id = request_id
        # Ensure ASGI scope has state for downstream ASGI middleware
        if hasattr(request, 'scope') and isinstance(request.scope, dict):
            request.scope.setdefault('state', {})['request_id'] = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        # Option B: Inject request_id into ANY JSON dict response if missing (success + error).
        # NOTE: BaseHTTPMiddleware may wrap JSON responses as StreamingResponse; if we consume
        # body_iterator, we MUST rebuild a new JSONResponse or the client will receive an empty body.
        if response.media_type == "application/json":
            try:
                consumed = False
                body = getattr(response, "body", None)
                if body is None and hasattr(response, "body_iterator"):
                    consumed = True
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                if not body:
                    if consumed:
                        headers = dict(response.headers)
                        headers.pop("content-length", None)
                        new_resp = JSONResponse(content=None, status_code=response.status_code, headers=headers)
                        if getattr(response, "background", None):
                            new_resp.background = response.background
                        return new_resp
                    return response
                body_str = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body
                data = json.loads(body_str)
                injected = False
                if isinstance(data, dict) and "request_id" not in data:
                    data["request_id"] = request_id
                    injected = True
                if consumed or injected:
                    headers = dict(response.headers)
                    headers.pop("content-length", None)
                    new_resp = JSONResponse(content=data, status_code=response.status_code, headers=headers)
                    if getattr(response, "background", None):
                        new_resp.background = response.background
                    return new_resp
            except Exception:
                pass
        return response