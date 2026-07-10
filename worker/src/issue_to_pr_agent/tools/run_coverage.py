"""Tool: run the repo's coverage command inside the sandbox."""

from __future__ import annotations

from typing import Any

from .registry import ToolContext
from .run_shell import _exec


def run_coverage(ctx: ToolContext, *, command: str, timeout: float | None = 600) -> dict[str, Any]:
    return _exec(ctx, command, timeout)
