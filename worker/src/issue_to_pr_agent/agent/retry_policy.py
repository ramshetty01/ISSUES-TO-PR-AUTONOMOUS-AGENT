"""Retry a callable a few times before giving up (for transient tool failures)."""

from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def run_with_retries(fn: Callable[[], T], *, attempts: int = 2) -> T:
    last: Exception | None = None
    for _ in range(max(1, attempts)):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - retry any transient error
            last = exc
    assert last is not None
    raise last
