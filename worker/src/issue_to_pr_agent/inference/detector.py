"""Top-level detection entrypoint."""

from __future__ import annotations

from pathlib import Path

from .repo_facts import RepoFacts, detect_repo_facts


def detect(repo_dir: Path) -> RepoFacts:
    """Infer everything the build/test layer needs about a repo."""
    return detect_repo_facts(repo_dir)
