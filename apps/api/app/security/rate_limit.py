import time
import hmac
from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from typing import Callable

def get_client_ip(request: Request, trust_proxy: bool) -> str:
    if trust_proxy:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host or "unknown"


class RateLimiter:
    def __init__(self):
        self._store = {}

    def check(self, ip: str, route_name: str, limit: int):
        now = time.time()
        key = f"{route_name}:{ip}"
        window = int(now // 60)
        entry = self._store.get(key)
        if entry is None or entry[0] != window:
            self._store[key] = (window, 1)
        else:
            count = entry[1] + 1
            if count > limit:
                retry_after = 60 - int(now % 60)
                detail = {
                    "error": "Too many requests",
                    "reason": f"Rate limit exceeded for {route_name}",
                    "retry_after": retry_after
                }
                headers = {"Retry-After": str(retry_after)}
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail=detail,
                    headers=headers
                )
            self._store[key] = (window, count)

def safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
