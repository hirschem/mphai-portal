from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException




def error_response(
    error_code: str,
    message: str,
    request_id: Optional[str],
    status_code: int,
    *,
    error: Optional[dict] = None,
    include_detail: bool = False,
    detail_error: Optional[object] = None,  # can be str or dict
) -> JSONResponse:
    rid = request_id or str(uuid.uuid4())

    error_obj = error or {
        "code": error_code,  # legacy key expected by tests
        "error_code": error_code,
        "message": message,
        "request_id": rid,
    }

    payload = {
        "request_id": rid,
        "error_code": error_code,
        "message": message,
        "error": error_obj,
    }
    if include_detail:
        payload["detail"] = {"error": detail_error if detail_error is not None else error_obj}

    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers={"X-Request-ID": rid},
    )


def add_global_error_handlers(app) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        message = "; ".join(
            f"{'.'.join(str(x) for x in err.get('loc', []))}: {err.get('msg', '')}"
            for err in exc.errors()
        )
        return error_response("VALIDATION_ERROR", message, request_id, 422)

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)

        code = "HTTP_ERROR"
        if exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 405:
            code = "METHOD_NOT_ALLOWED"

        return error_response(code, str(getattr(exc, "detail", "")), request_id, exc.status_code)

    @app.exception_handler(HTTPException)
    async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)

        code = "HTTP_ERROR"
        if exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"

        return error_response(code, str(getattr(exc, "detail", "")), request_id, exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        return error_response("INTERNAL_ERROR", "Internal server error", request_id, 500)
