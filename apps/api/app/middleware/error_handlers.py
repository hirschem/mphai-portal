from __future__ import annotations

import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.types import ASGIApp

def add_global_error_handlers(app: ASGIApp) -> None:
    """
    Adds a global error handler that injects request_id into all error responses.
    """
    async def error_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        detail = str(exc)
        if hasattr(exc, "errors") and hasattr(exc, "status_code"):
            # Pydantic/RequestValidationError
            status_code = getattr(exc, "status_code", status.HTTP_422_UNPROCESSABLE_ENTITY)
            detail = getattr(exc, "errors", lambda: detail)()
        elif hasattr(exc, "status_code"):
            status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logging.getLogger("mph.error").error(traceback.format_exc())
        # --- PATCH: Add CORS headers for allowed origins ---
        origin = request.headers.get("origin")
        headers = None
        if origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Vary": "Origin",
            }
        # --- END PATCH ---
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": detail,
                "request_id": request_id,
            },
            headers=headers,
        )
    app.add_exception_handler(Exception, error_handler)
    # Patch Starlette's ServerErrorMiddleware to not swallow our handler
    if hasattr(app, "user_middleware"):
        for m in app.user_middleware:
            if isinstance(m, ServerErrorMiddleware):
                m.debug = True
