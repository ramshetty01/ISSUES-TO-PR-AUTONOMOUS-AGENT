"""Context manager guaranteeing sandbox teardown even on failure."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterator

from .base import Sandbox


@contextmanager
def sandbox_session(sandbox: Sandbox) -> Iterator[Sandbox]:
    """Start the sandbox, yield it, and always tear it down."""
    sandbox.start()
    try:
        yield sandbox
    finally:
        sandbox.teardown()
