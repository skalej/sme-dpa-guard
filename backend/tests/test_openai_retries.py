from __future__ import annotations

import pytest

from app.services.openai_retry import is_transient_openai_exception, retry_with_backoff


class DummyTransientError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__("transient")
        self.status_code = status_code


def test_retry_succeeds_after_transient_failures() -> None:
    calls = {"count": 0}

    def _fn() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise DummyTransientError(429)
        return "OK"

    result = retry_with_backoff(_fn, sleep_fn=lambda _delay: None)
    assert result == "OK"
    assert calls["count"] == 3


def test_retry_exhausted_raises() -> None:
    calls = {"count": 0}

    def _fn() -> str:
        calls["count"] += 1
        raise DummyTransientError(503)

    with pytest.raises(DummyTransientError):
        retry_with_backoff(_fn, sleep_fn=lambda _delay: None)
    assert calls["count"] == 3


def test_non_transient_not_retried() -> None:
    calls = {"count": 0}

    def _fn() -> str:
        calls["count"] += 1
        raise ValueError("bad request")

    with pytest.raises(ValueError):
        retry_with_backoff(_fn, sleep_fn=lambda _delay: None)
    assert calls["count"] == 1


def test_is_transient_exception_status_code() -> None:
    assert is_transient_openai_exception(DummyTransientError(429)) is True
