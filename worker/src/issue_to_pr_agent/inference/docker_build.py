"""Build the synthesized image, capturing failures for the improvements report."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..sandbox.command_runner import CommandResult, run_command

BuildRunner = Callable[[list[str], Path], CommandResult]


def _default_runner(argv: list[str], cwd: Path) -> CommandResult:
    return run_command(argv, cwd=cwd)


@dataclass(slots=True)
class BuildResult:
    success: bool
    tag: str
    logs: str


def build_image(
    dockerfile: str,
    context_dir: Path,
    tag: str,
    *,
    runner: BuildRunner = _default_runner,
    dockerfile_name: str = "Dockerfile.itpr",
) -> BuildResult:
    """Write the Dockerfile into the context and run `docker build`."""
    dockerfile_path = context_dir / dockerfile_name
    dockerfile_path.write_text(dockerfile, encoding="utf-8")
    res = runner(
        ["docker", "build", "-f", str(dockerfile_path), "-t", tag, str(context_dir)],
        context_dir,
    )
    logs = (res.stdout + res.stderr).strip()
    return BuildResult(success=res.exit_code == 0, tag=tag, logs=logs)
