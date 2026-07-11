"""Sandbox factory. Returns the local Docker sandbox; the base interface keeps
the door open for cloud providers later.
"""

from __future__ import annotations

import os
from pathlib import Path

from .base import Sandbox
from .limits import SandboxLimits
from .local_process import LocalProcessSandbox
from .local_docker import LocalDockerSandbox


def create_sandbox(
    image: str, workspace: Path, *, limits: SandboxLimits | None = None
) -> Sandbox:
    if os.environ.get("ITPR_SANDBOX_MODE") == "process":
        return LocalProcessSandbox(workspace)
    return LocalDockerSandbox(image, workspace, limits=limits)
