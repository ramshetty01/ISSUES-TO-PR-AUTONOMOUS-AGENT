"""Sandbox factory. Returns the local Docker sandbox; the base interface keeps
the door open for cloud providers later.
"""

from __future__ import annotations

from pathlib import Path

from .base import Sandbox
from .limits import SandboxLimits
from .local_docker import LocalDockerSandbox


def create_sandbox(
    image: str, workspace: Path, *, limits: SandboxLimits | None = None
) -> Sandbox:
    return LocalDockerSandbox(image, workspace, limits=limits)
