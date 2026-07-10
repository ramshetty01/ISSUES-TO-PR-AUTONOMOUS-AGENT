"""Best-effort test/framework detection from dependency manifests."""

from __future__ import annotations

from pathlib import Path

from .language_detector import Language


def detect_framework(repo_dir: Path, language: Language) -> str | None:
    if language == "python":
        text = _read(repo_dir, "pyproject.toml") + _read(repo_dir, "requirements.txt")
        for fw in ("pytest", "django", "flask", "fastapi", "unittest"):
            if fw in text:
                return fw
        return "pytest"  # sensible default for python repos
    if language == "node":
        pkg = _read(repo_dir, "package.json")
        for fw in ("vitest", "jest", "mocha", "next", "react"):
            if fw in pkg:
                return fw
        return None
    return None


def _read(repo_dir: Path, name: str) -> str:
    p = repo_dir / name
    return p.read_text(encoding="utf-8") if p.exists() else ""
