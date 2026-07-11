"""In-container process sandbox for worker-container execution.

The dispatcher already starts the worker inside a constrained Docker container.
In that mode, running commands directly in the checked-out workspace avoids a
nested Docker daemon and keeps file edits on the same filesystem the worker owns.
"""

from __future__ import annotations

from pathlib import Path

from .base import Sandbox
from .command_runner import CommandResult, run_command
from .filesystem import PathJail


class LocalProcessSandbox(Sandbox):
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace.resolve()
        self._jail = PathJail(self._workspace)

    @property
    def workspace(self) -> Path:
        return self._workspace

    def start(self) -> None:
        self._workspace.mkdir(parents=True, exist_ok=True)

    def exec(self, argv: list[str], *, timeout: float | None = None) -> CommandResult:
        return run_command(argv, cwd=self._workspace, timeout=timeout)

    def read_file(self, relpath: str) -> str:
        return self._jail.read_text(relpath)

    def write_file(self, relpath: str, content: str) -> None:
        self._jail.write_text(relpath, content)

    def teardown(self) -> None:
        pass
