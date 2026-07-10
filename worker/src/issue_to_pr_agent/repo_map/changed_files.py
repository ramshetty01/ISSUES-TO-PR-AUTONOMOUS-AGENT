"""Files changed relative to a base ref (via git)."""

from __future__ import annotations

from pathlib import Path

from ..github.clone import GitRunner


def changed_files(runner: GitRunner, repo_dir: Path, base_ref: str = "HEAD") -> list[str]:
    """Repo-relative paths changed vs `base_ref` (name-only diff)."""
    res = runner.run(["diff", "--name-only", base_ref], cwd=repo_dir)
    if res.returncode != 0:
        return []
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]
