
import json
import logging
import time
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("mph.request")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response: Response
        try:
            response = await call_next(request)
        finally:
            duration_ms = int((time.time() - start) * 1000)
            req_id = getattr(request.state, "request_id", None)
            method = request.method
            path = request.url.path
            status_code = getattr(getattr(request, "scope", {}), "get", lambda *_: None)("status") or None
            client_ip = request.client.host if request.client else None
            role = getattr(request.state, "role", None)
            content_length = request.headers.get("content-length")
            payload = {
                "request_id": req_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "role": role if role in ("demo", "admin") else None,
                "content_length": content_length if content_length is not None else None,
            }
            if "response" in locals() and response is not None:
                payload["status_code"] = response.status_code
            logger.info(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
        return response
