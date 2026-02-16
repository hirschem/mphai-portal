
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
        method = request.method
        path = request.url.path
        logger.info(json.dumps({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": "INFO",
            "request_id": req_id,
            "event": "request_start",
            "method": method,
            "path": path,
        }))
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
            }))
        return response
        return response
