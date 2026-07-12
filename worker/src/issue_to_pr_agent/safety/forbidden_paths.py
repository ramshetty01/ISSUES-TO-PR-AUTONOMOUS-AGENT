"""Refuse edits to forbidden paths (CI workflows, secrets, .git)."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from .refusal import refuse

DEFAULT_FORBIDDEN = [
    ".github/workflows/",
    ".github/actions/",
    ".git/",
    ".env",
    "secrets/",
]


def _normalize(path: str) -> str:
    return path[2:] if path.startswith("./") else path


def is_forbidden(path: str, forbidden: list[str] = DEFAULT_FORBIDDEN) -> bool:
    norm = _normalize(path)
    return any(norm.startswith(f) or f.rstrip("/") == norm for f in forbidden)


def assert_path_allowed(path: str, forbidden: list[str] = DEFAULT_FORBIDDEN) -> None:
    if is_forbidden(path, forbidden):
        raise refuse("forbidden_path", "edit to a forbidden path", path)


def load_forbidden(path: str | Path) -> list[str]:
    import yaml

    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return cast(list[str], doc.get("forbidden", DEFAULT_FORBIDDEN))
