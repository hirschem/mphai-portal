from starlette.types import ASGIApp, Receive, Scope, Send
import json
import os

class EnforceRequestIDInJSONErrorsMiddleware:
    def __init__(self, app: ASGIApp, max_buffer_size: int = 256 * 1024):
        self.app = app
        self.max_buffer_size = max_buffer_size
        self.debug = os.getenv("ENFORCE_REQID_DEBUG", "0") == "1"

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_status = None
        response_headers = None
        body_chunks = []
        body_size = 0
        buffering = False
        sent = False
        content_type = None

        def log_debug(**kwargs):
            if self.debug:
                print("[ENFORCE_REQID] " + ", ".join(f"{k}={v}" for k, v in kwargs.items()))

        async def send_wrapper(message):
            nonlocal response_status, response_headers, body_chunks, body_size, sent, buffering, content_type
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message["headers"]
                for k, v in response_headers:
                    if k.lower() == b"content-type":
                        content_type = v.decode().lower()
                        break
                buffering = (
                    response_status >= 400
                    and content_type
                    and "application/json" in content_type
                )
                log_debug(status_code=response_status, content_type=content_type, buffering=buffering)
                if not buffering:
                    await send(message)
            elif message["type"] == "http.response.body" and buffering:
                chunk = message.get("body", b"")
                body_chunks.append(chunk)
                body_size += len(chunk)
                more_body = message.get("more_body", False)
                log_debug(buffered_bytes=body_size, more_body=more_body)
                if body_size > self.max_buffer_size:
                    log_debug(buffering="disabled (too large)")
                    # Too large, passthrough
                    await send({"type": "http.response.start", "status": response_status, "headers": response_headers})
                    for c in body_chunks:
                        await send({"type": "http.response.body", "body": c, "more_body": False})
                    sent = True
                    return
                if more_body:
                    return
                # All body received, parse and possibly inject request_id
                body = b"".join(body_chunks)
                try:
                    data = json.loads(body.decode("utf-8"))
                    is_dict = isinstance(data, dict)
                except Exception:
                    log_debug(json_parse="fail")
                    # Fallback: passthrough
                    await send({"type": "http.response.start", "status": response_status, "headers": response_headers})
                    for c in body_chunks:
                        await send({"type": "http.response.body", "body": c, "more_body": False})
                    sent = True
                    return
                log_debug(json_parse="ok", is_dict=is_dict)
                injected = False
                taxonomy = {
                    401: "UNAUTHORIZED",
                    403: "FORBIDDEN",
                    404: "NOT_FOUND",
                    413: "PAYLOAD_TOO_LARGE",
                    422: "VALIDATION_ERROR",
                    500: "INTERNAL_ERROR",
                }
                # Always inject request_id if missing
                if is_dict:
                    # DEBUG: log before modification for 401 /test-direct-json-error
                    # request_id
                    if "request_id" not in data:
                        rid = scope.get("state", {}).get("request_id")
                        if not rid:
                            for k, v in response_headers:
                                if k.lower() == b"x-request-id":
                                    rid = v.decode()
                                    break
                        if rid:
                            data["request_id"] = rid
                            injected = True
                    # error_code
                    if "error_code" not in data:
                        code = taxonomy.get(response_status)
                        if not code:
                            if 400 <= response_status < 500:
                                code = "HTTP_ERROR"
                            else:
                                code = "INTERNAL_ERROR"
                        data["error_code"] = code
                        injected = True
                    # message precedence: detail > existing message (not 'fail') > fallback
                    detail = data.get("detail")
                    msg = data.get("message")
                    # If detail is a non-empty string, always use it
                    if isinstance(detail, str) and detail.strip():
                        data["message"] = detail
                        injected = True
                    # Else if message is missing, empty, or 'fail', use fallback
                    elif not (isinstance(msg, str) and msg.strip() and msg != "fail"):
                        if isinstance(detail, (list, dict)):
                            data["message"] = "Validation error"
                        else:
                            fallback_msgs = {
                                401: "Unauthorized",
                                403: "Forbidden",
                                404: "Not found",
                                413: "Payload too large",
                                422: "Validation error",
                                500: "Internal server error",
                            }
                            data["message"] = fallback_msgs.get(response_status) or "Error"
                        injected = True
                    # Else, keep existing message
                log_debug(request_id_injected="request_id" in data, error_code_injected="error_code" in data, message_injected="message" in data)
                if injected:
                    new_body = json.dumps(data, separators=(",", ":")).encode("utf-8")
                    # Update Content-Length
                    new_headers = [
                        (k, v) if k.lower() != b"content-length" else (k, str(len(new_body)).encode())
                        for k, v in response_headers
                    ]
                    await send({"type": "http.response.start", "status": response_status, "headers": new_headers})
                    await send({"type": "http.response.body", "body": new_body, "more_body": False})
                    sent = True
                    return
                # Not injected, passthrough
                await send({"type": "http.response.start", "status": response_status, "headers": response_headers})
                for c in body_chunks:
                    await send({"type": "http.response.body", "body": c, "more_body": False})
                sent = True
                return
            else:
                await send(message)

        await self.app(scope, receive, send_wrapper)
