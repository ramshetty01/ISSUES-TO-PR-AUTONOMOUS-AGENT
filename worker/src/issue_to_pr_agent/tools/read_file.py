"""Tool: read a file (path-jailed via the sandbox)."""

from __future__ import annotations

from typing import Any

from .registry import ToolContext


def read_file(ctx: ToolContext, *, path: str) -> dict[str, Any]:
    content = ctx.sandbox.read_file(path)
    return {"ok": True, "path": path, "content": content}
