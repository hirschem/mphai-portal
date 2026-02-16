
from __future__ import annotations

def error_response(code: str, message: str, request_id: str, status_code: int):
    resp = JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )
    if request_id:
        resp.headers["X-Request-ID"] = str(request_id)
    return resp

import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.types import ASGIApp

def add_global_error_handlers(app: ASGIApp) -> None:
    from fastapi import HTTPException
    import uuid

    async def http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)
        if not request_id:
            request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        status_code = exc.status_code
        if status_code == 401:
            code = "UNAUTHORIZED"
        elif status_code == 403:
            code = "FORBIDDEN"
        elif status_code == 404:
            code = "NOT_FOUND"
        else:
            code = "HTTP_ERROR"
        message = str(exc.detail)
        origin = request.headers.get("origin")
        headers = {"X-Request-ID": str(request_id)}
        if origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": request_id,
                }
            },
            headers=headers
        )

    # Adds a global error handler that injects request_id into all error responses.
    async def error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        if hasattr(exc, "status_code"):
            status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        code = getattr(exc, "code", exc.__class__.__name__)
        message = str(exc)
        # CORS headers for allowed origins
        origin = request.headers.get("origin")
        headers = None
        if origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Vary": "Origin",
            }
        logging.getLogger("mph.error").error(traceback.format_exc())
        resp = error_response(code, message, request_id, status_code)
        if headers:
            resp.headers.update(headers)
        return resp

    app.add_exception_handler(Exception, error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    # Patch Starlette's ServerErrorMiddleware to not swallow our handler
    if hasattr(app, "user_middleware"):
        for m in app.user_middleware:
            if isinstance(m, ServerErrorMiddleware):
                m.debug = True
