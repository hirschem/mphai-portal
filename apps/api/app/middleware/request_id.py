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
        request_id = incoming.strip() if incoming else str(uuid.uuid4())
        request.state.request_id = request_id
        # Ensure ASGI scope has state for downstream ASGI middleware
        if hasattr(request, 'scope') and isinstance(request.scope, dict):
            request.scope.setdefault('state', {})['request_id'] = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        # If this is a JSON error response (status >= 400), inject request_id if missing
        if response.status_code >= 400 and response.media_type == "application/json":
            try:
                # Try to get the body (works for JSONResponse and most responses)
                body = None
                if hasattr(response, "body") and response.body is not None:
                    body = response.body
                elif hasattr(response, "render"):
                    # For JSONResponse, render() returns the body
                    body = response.render(response.body)
                elif hasattr(response, "body_iterator"):
                    # For streaming responses
                    body = b"".join([chunk async for chunk in response.body_iterator])
                if not body:
                    return response
                data = json.loads(body)
                if isinstance(data, dict) and "request_id" not in data:
                    data["request_id"] = request_id
                    # Rebuild the response with the new body and preserve headers
                    new_resp = JSONResponse(content=data, status_code=response.status_code, headers=dict(response.headers))
                    # Preserve background task if present
                    if getattr(response, "background", None):
                        new_resp.background = response.background
                    return new_resp
            except Exception:
                pass  # If anything fails, return original response
        return response
