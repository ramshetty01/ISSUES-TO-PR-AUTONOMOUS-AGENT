"""Lightweight symbol index.

A full tree-sitter grammar set is heavy; this uses language-aware regexes to
extract top-level definitions (functions/classes). The interface is stable so a
real tree-sitter backend can slot in later without changing callers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .tree import list_files

_PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    ".py": [
        ("function", re.compile(r"^\s*def\s+([A-Za-z_]\w*)")),
        ("class", re.compile(r"^\s*class\s+([A-Za-z_]\w*)")),
    ],
    ".js": [
        ("function", re.compile(r"^\s*(?:export\s+)?function\s+([A-Za-z_]\w*)")),
        ("const", re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z_]\w*)\s*=")),
    ],
    ".ts": [
        ("function", re.compile(r"^\s*(?:export\s+)?function\s+([A-Za-z_]\w*)")),
        ("class", re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_]\w*)")),
    ],
    ".go": [("function", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"))],
    ".rs": [("function", re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)"))],
}
_PATTERNS[".jsx"] = _PATTERNS[".js"]
_PATTERNS[".tsx"] = _PATTERNS[".ts"]


@dataclass(slots=True, frozen=True)
class Symbol:
    name: str
    kind: str
    file: str
    line: int


def index_symbols(repo_dir: Path) -> list[Symbol]:
    symbols: list[Symbol] = []
    for rel in list_files(repo_dir):
        patterns = _PATTERNS.get(rel.suffix)
        if not patterns:
            continue
        try:
            content = (repo_dir / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(content.splitlines(), start=1):
            for kind, rx in patterns:
                m = rx.match(line)
                if m:
                    symbols.append(Symbol(m.group(1), kind, str(rel), i))
    return symbols
