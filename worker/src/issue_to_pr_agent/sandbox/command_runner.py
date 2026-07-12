"""Run commands with captured output + a hard timeout."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


def run_command(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    """Run argv, capturing output. On timeout returns timed_out=True, exit 124."""
    try:
        proc = subprocess.run(  # noqa: S603 - argv is a list, not a shell string
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr or ""
        return CommandResult(124, stdout, stderr, timed_out=True)
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)
