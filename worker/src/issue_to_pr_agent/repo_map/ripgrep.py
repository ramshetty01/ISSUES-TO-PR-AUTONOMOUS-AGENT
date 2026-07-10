"""Content search via ripgrep, with a pure-Python fallback when rg is absent."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .tree import list_files


@dataclass(slots=True)
class Match:
    file: str
    line: int
    text: str


def _search_python(repo_dir: Path, pattern: str, max_results: int) -> list[Match]:
    rx = re.compile(pattern)
    out: list[Match] = []
    for rel in list_files(repo_dir):
        try:
            content = (repo_dir / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(content.splitlines(), start=1):
            if rx.search(line):
                out.append(Match(str(rel), i, line.strip()))
                if len(out) >= max_results:
                    return out
    return out


def search(repo_dir: Path, pattern: str, *, max_results: int = 200) -> list[Match]:
    """Search file contents for `pattern`. Uses rg if available, else Python."""
    if shutil.which("rg") is None:
        return _search_python(repo_dir, pattern, max_results)
    proc = subprocess.run(  # noqa: S603
        ["rg", "--line-number", "--no-heading", "--color=never", pattern, str(repo_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode not in (0, 1):  # 1 = no matches
        return _search_python(repo_dir, pattern, max_results)
    out: list[Match] = []
    for line in proc.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path, lineno, text = parts
        try:
            rel = str(Path(path).resolve().relative_to(repo_dir.resolve()))
        except ValueError:
            rel = path
        out.append(Match(rel, int(lineno), text.strip()))
        if len(out) >= max_results:
            break
    return out
