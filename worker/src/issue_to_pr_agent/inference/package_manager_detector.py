"""Detect the package manager, given the language + lockfiles."""

from __future__ import annotations

from pathlib import Path

from .language_detector import Language


def detect_package_manager(repo_dir: Path, language: Language) -> str:
    if language == "python":
        if (repo_dir / "uv.lock").exists():
            return "uv"
        if (repo_dir / "poetry.lock").exists() or _has_poetry_table(repo_dir):
            return "poetry"
        return "pip"
    if language == "node":
        if (repo_dir / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (repo_dir / "yarn.lock").exists():
            return "yarn"
        return "npm"
    if language == "java":
        if (repo_dir / "pom.xml").exists():
            return "maven"
        return "gradle"
    if language == "go":
        return "go"
    if language == "rust":
        return "cargo"
    return "unknown"


def _has_poetry_table(repo_dir: Path) -> bool:
    pyproject = repo_dir / "pyproject.toml"
    if not pyproject.exists():
        return False
    return "[tool.poetry]" in pyproject.read_text(encoding="utf-8")
