"""Tool: write a file (path-jailed via the sandbox)."""

from __future__ import annotations

from typing import Any

from .registry import ToolContext


def write_file(ctx: ToolContext, *, path: str, content: str) -> dict[str, Any]:
    ctx.sandbox.write_file(path, content)
    return {"ok": True, "path": path, "bytes": len(content)}
