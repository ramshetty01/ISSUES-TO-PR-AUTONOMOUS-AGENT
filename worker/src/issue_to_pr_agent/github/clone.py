"""Git runner abstraction + repository clone.

A GitRunner runs git subcommands; the default shells out, tests inject a fake so
no real git/network is needed. The clone URL embeds a short-lived installation
token (standard x-access-token form).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..errors import SandboxError
from ..job import Repo


@dataclass(slots=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


class GitRunner(Protocol):
    def run(self, args: list[str], cwd: Path | None = None) -> GitResult: ...


class SubprocessGitRunner:
    """Default GitRunner: shells out to the git binary."""

    def run(self, args: list[str], cwd: Path | None = None) -> GitResult:
        proc = subprocess.run(  # noqa: S603 - args are constructed, not shell
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return GitResult(proc.returncode, proc.stdout, proc.stderr)


def authed_url(repo: Repo, token: str) -> str:
    """HTTPS clone URL with an embedded installation token."""
    return f"https://x-access-token:{token}@github.com/{repo.owner}/{repo.name}.git"


def clone_repo(
    runner: GitRunner,
    repo: Repo,
    token: str,
    dest: Path,
    *,
    depth: int | None = 1,
) -> Path:
    """Clone `repo` into `dest`. Raises SandboxError on failure."""
    args = ["clone"]
    if depth:
        args += ["--depth", str(depth)]
    args += [authed_url(repo, token), str(dest)]
    res = runner.run(args)
    if res.returncode != 0:
        # Never echo the token-bearing URL in errors.
        raise SandboxError(f"git clone failed (exit {res.returncode})")
    return dest
