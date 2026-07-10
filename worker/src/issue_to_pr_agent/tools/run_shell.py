"""Tool: run a shell command inside the sandbox."""

from __future__ import annotations

from typing import Any

from .registry import ToolContext


def _exec(ctx: ToolContext, command: str, timeout: float | None) -> dict[str, Any]:
    res = ctx.sandbox.exec(["sh", "-c", command], timeout=timeout)
    return {
        "ok": res.exit_code == 0 and not res.timed_out,
        "exit_code": res.exit_code,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "timed_out": res.timed_out,
    }


def run_shell(ctx: ToolContext, *, command: str, timeout: float | None = 120) -> dict[str, Any]:
    return _exec(ctx, command, timeout)
