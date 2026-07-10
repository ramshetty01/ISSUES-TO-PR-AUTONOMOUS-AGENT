"""Tool: find symbol definitions by name."""

from __future__ import annotations

from typing import Any

from ..repo_map.symbol_graph import build_symbol_graph
from .registry import ToolContext


def tree_sitter_search(ctx: ToolContext, *, name: str) -> dict[str, Any]:
    graph = build_symbol_graph(ctx.repo_dir)
    hits = graph.lookup(name)
    return {
        "ok": True,
        "symbols": [
            {"name": s.name, "kind": s.kind, "file": s.file, "line": s.line} for s in hits
        ],
    }
