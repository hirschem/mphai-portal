
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
        import datetime
        start = time.time()
        req_id = getattr(request.state, "request_id", None)
        if not req_id or not str(req_id).strip():
            header_id = request.headers.get("x-request-id", "").strip()
            if header_id:
                req_id = header_id
            else:
                import uuid
                req_id = str(uuid.uuid4())
            request.state.request_id = req_id
            if hasattr(request, 'scope') and isinstance(request.scope, dict):
                request.scope.setdefault('state', {})['request_id'] = req_id
        method = request.method
        path = request.url.path
        logger.info(json.dumps({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "INFO",
            "request_id": req_id,
            "event": "request_start",
            "method": method,
            "path": path,
        }), extra={"request_id": req_id})
        response: Response
        try:
            response = await call_next(request)
        finally:
            duration_ms = int((time.time() - start) * 1000)
            status_code = getattr(response, "status_code", None) if 'response' in locals() else None
            logger.info(json.dumps({
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "level": "INFO",
                "request_id": req_id,
                "event": "request_end",
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }), extra={"request_id": req_id})
        return response
