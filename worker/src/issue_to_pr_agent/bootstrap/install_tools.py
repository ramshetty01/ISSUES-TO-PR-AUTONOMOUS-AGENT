"""Ensure the external tools the worker relies on are available."""

from __future__ import annotations

import shutil
from collections.abc import Iterable

from ..errors import BootstrapError

REQUIRED_TOOLS = ("git", "rg")


def ensure_tools(tools: Iterable[str] = REQUIRED_TOOLS) -> None:
    """Raise BootstrapError listing any required tool not on PATH."""
    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        raise BootstrapError(f"required tools not found on PATH: {', '.join(missing)}")
