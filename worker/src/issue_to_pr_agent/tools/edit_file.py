"""Tool: replace an exact substring in a file (search/replace edit)."""

from __future__ import annotations

from typing import Any

from ..errors import SandboxError
from .registry import ToolContext


def edit_file(ctx: ToolContext, *, path: str, old: str, new: str) -> dict[str, Any]:
    content = ctx.sandbox.read_file(path)
    count = content.count(old)
    if count == 0:
        raise SandboxError(f"edit_file: `old` not found in {path}")
    if count > 1:
        raise SandboxError(f"edit_file: `old` is not unique in {path} ({count} matches)")
    ctx.sandbox.write_file(path, content.replace(old, new, 1))
    return {"ok": True, "path": path, "replaced": 1}
