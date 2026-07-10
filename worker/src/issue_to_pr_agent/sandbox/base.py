"""The Sandbox interface. Kept abstract so cloud providers can slot in later;
local_docker.py is THE implementation for the $0 build.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .command_runner import CommandResult


class Sandbox(ABC):
    """An isolated environment for running the agent's commands + file edits."""

    @property
    @abstractmethod
    def workspace(self) -> Path: ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def exec(self, argv: list[str], *, timeout: float | None = None) -> CommandResult: ...

    @abstractmethod
    def read_file(self, relpath: str) -> str: ...

    @abstractmethod
    def write_file(self, relpath: str, content: str) -> None: ...

    @abstractmethod
    def teardown(self) -> None: ...
