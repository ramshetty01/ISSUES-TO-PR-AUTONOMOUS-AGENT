"""Per-file import edges (a coarse dependency graph)."""

from __future__ import annotations

import re
from pathlib import Path

from .tree import list_files

_PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))")
_JS_IMPORT = re.compile(r"""(?:import\s.*?from\s+|require\()\s*['"]([^'"]+)['"]""")


def _imports_for(path: Path, content: str) -> set[str]:
    deps: set[str] = set()
    if path.suffix == ".py":
        for line in content.splitlines():
            m = _PY_IMPORT.match(line)
            if m:
                deps.add((m.group(1) or m.group(2)).split(".")[0])
    elif path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
        for m in _JS_IMPORT.finditer(content):
            deps.add(m.group(1))
    return deps


def build_dependency_graph(repo_dir: Path) -> dict[str, set[str]]:
    """Map each source file (repo-relative) to the modules it imports."""
    graph: dict[str, set[str]] = {}
    for rel in list_files(repo_dir):
        if rel.suffix not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
            continue
        try:
            content = (repo_dir / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        deps = _imports_for(rel, content)
        if deps:
            graph[str(rel)] = deps
    return graph
