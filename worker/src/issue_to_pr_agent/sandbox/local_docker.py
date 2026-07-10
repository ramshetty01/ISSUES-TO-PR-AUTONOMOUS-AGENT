"""Local Docker sandbox — THE implementation. Commands run inside a constrained
container; files are edited on the mounted workspace through a path jail.

The docker executor is injectable so the arg construction + lifecycle can be
tested without a real daemon.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ..errors import SandboxError
from .base import Sandbox
from .command_runner import CommandResult, run_command
from .filesystem import PathJail
from .limits import SandboxLimits

DockerExec = Callable[[list[str]], CommandResult]

CONTAINER_WORKDIR = "/workspace"


def _default_exec(argv: list[str]) -> CommandResult:
    return run_command(argv)


class LocalDockerSandbox(Sandbox):
    def __init__(
        self,
        image: str,
        workspace: Path,
        *,
        limits: SandboxLimits | None = None,
        container_name: str | None = None,
        docker: DockerExec = _default_exec,
    ) -> None:
        self._image = image
        self._workspace = workspace.resolve()
        self._limits = limits or SandboxLimits()
        self._name = container_name or f"itpr-sbx-{self._workspace.name}"
        self._docker = docker
        self._jail = PathJail(self._workspace)
        self._started = False

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def container_name(self) -> str:
        return self._name

    def build_run_args(self) -> list[str]:
        """The `docker run` argv (pure; exercised directly in tests)."""
        return [
            "docker", "run", "-d",
            "--name", self._name,
            *self._limits.to_docker_args(),
            "-v", f"{self._workspace}:{CONTAINER_WORKDIR}",
            "-w", CONTAINER_WORKDIR,
            self._image,
            "sleep", "infinity",
        ]

    def start(self) -> None:
        res = self._docker(self.build_run_args())
        if res.exit_code != 0:
            raise SandboxError(f"failed to start sandbox container ({res.exit_code})")
        self._started = True

    def exec(self, argv: list[str], *, timeout: float | None = None) -> CommandResult:
        if not self._started:
            raise SandboxError("sandbox not started")
        return self._docker(["docker", "exec", self._name, *argv])

    def read_file(self, relpath: str) -> str:
        return self._jail.read_text(relpath)

    def write_file(self, relpath: str, content: str) -> None:
        self._jail.write_text(relpath, content)

    def teardown(self) -> None:
        # Best-effort: never raise from teardown.
        try:
            self._docker(["docker", "rm", "-f", self._name])
        finally:
            self._started = False
