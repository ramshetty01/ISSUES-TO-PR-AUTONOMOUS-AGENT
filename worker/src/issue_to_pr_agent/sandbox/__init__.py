"""Sandbox: isolated command execution + path-jailed file access."""

from .base import Sandbox
from .command_runner import CommandResult, run_command
from .filesystem import PathJail
from .lifecycle import sandbox_session
from .limits import SandboxLimits
from .local_docker import LocalDockerSandbox
from .manager import create_sandbox
from .network_policy import NetworkPolicy, blocks_egress

__all__ = [
    "Sandbox",
    "CommandResult",
    "run_command",
    "PathJail",
    "sandbox_session",
    "SandboxLimits",
    "LocalDockerSandbox",
    "create_sandbox",
    "NetworkPolicy",
    "blocks_egress",
]
