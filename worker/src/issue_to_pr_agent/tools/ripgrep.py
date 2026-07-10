"""Tool: content search across the repo."""

from __future__ import annotations

from typing import Any

from ..repo_map.ripgrep import search
from .registry import ToolContext


def ripgrep_tool(ctx: ToolContext, *, pattern: str, max_results: int = 50) -> dict[str, Any]:
    matches = search(ctx.repo_dir, pattern, max_results=max_results)
    return {
        "ok": True,
        "matches": [{"file": m.file, "line": m.line, "text": m.text} for m in matches],
    }
