from __future__ import annotations

import random
import time
from typing import Callable, TypeVar

T = TypeVar("T")


class TransientOpenAIError(Exception):
    pass


def _exception_name(exc: Exception) -> str:
    return exc.__class__.__name__


def is_transient_openai_exception(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        if status_code == 429 or 500 <= status_code <= 599:
            return True

    name = _exception_name(exc)
    transient_names = {
        "RateLimitError",
        "APITimeoutError",
        "APIConnectionError",
        "InternalServerError",
        "ServiceUnavailableError",
        "APIError",
        "TimeoutError",
        "ConnectionError",
    }
    if name in transient_names:
        return True

    cause = getattr(exc, "__cause__", None)
    if isinstance(cause, Exception):
        return is_transient_openai_exception(cause)

    return False


def retry_with_backoff(
    fn: Callable[[], T],
    *,
    max_retries: int = 2,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    attempt = 0
    while True:
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if not is_transient_openai_exception(exc) or attempt >= max_retries:
                raise
            jitter = random.uniform(0, 0.2)
            delay = min(max_delay, base_delay * (2**attempt) + jitter)
            sleep_fn(delay)
            attempt += 1
