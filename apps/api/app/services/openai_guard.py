import asyncio
import random


class OpenAIFailure(Exception):
    """Typed exception for OpenAI call failures with stable .code property."""
    def __init__(self, code, message, attempts):
        super().__init__(message)
        self.code = code
        self.message = message
        self.attempts = attempts

def is_retryable(exc):
    import openai
    return isinstance(exc, (
        openai.RateLimitError,
        openai.APIError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        asyncio.TimeoutError,
    ))

async def call_openai_with_retry(fn, max_attempts=3, per_attempt_timeout_s=20.0):
    import openai
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await asyncio.wait_for(fn(), timeout=per_attempt_timeout_s)
        except Exception as e:
            last_exc = e
            # Map to stable code
            if isinstance(e, openai.RateLimitError):
                code = "OPENAI_RATE_LIMITED"
            elif isinstance(e, (openai.APIError, openai.APIConnectionError)):
                code = "OPENAI_UPSTREAM_ERROR"
            elif isinstance(e, (openai.APITimeoutError, asyncio.TimeoutError)):
                code = "OPENAI_TIMEOUT"
            else:
                code = "OPENAI_UNKNOWN_ERROR"
            if not is_retryable(e) or attempt == max_attempts:
                raise OpenAIFailure(code, str(last_exc), attempt)
        # Exponential backoff with jitter (max 4s)
        sleep_s = min(0.5 * (2 ** (attempt - 1)), 4.0)
        sleep_s = sleep_s * (0.8 + 0.4 * random.random())
        await asyncio.sleep(sleep_s)
