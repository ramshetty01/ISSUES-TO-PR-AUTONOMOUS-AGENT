"""Detect the primary language of a repository from marker files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

Language = Literal["python", "node", "go", "rust", "java", "unknown"]

# (marker filename, language) in priority order.
_MARKERS: list[tuple[str, Language]] = [
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("setup.cfg", "python"),
    ("requirements.txt", "python"),
    ("package.json", "node"),
    ("go.mod", "go"),
    ("Cargo.toml", "rust"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
    ("build.gradle.kts", "java"),
]


def detect_language(repo_dir: Path) -> Language:
    for marker, lang in _MARKERS:
        if (repo_dir / marker).exists():
            return lang
    # Fall back to source-extension sniffing.
    if any(repo_dir.glob("**/*.py")):
        return "python"
    if any(repo_dir.glob("**/*.go")):
        return "go"
    if any(repo_dir.glob("**/*.rs")):
        return "rust"
    return "unknown"
