"""Worker exception hierarchy."""

from __future__ import annotations


class WorkerError(Exception):
    """Base class for all worker errors."""


class BootstrapError(WorkerError):
    """Raised when startup (job load/validation, workspace, tools) fails."""


class SandboxError(WorkerError):
    """Raised when sandboxed command execution fails or violates isolation."""


class SafetyRefusal(WorkerError):
    """Raised when a safety policy blocks an operation. Terminal by design."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class VerificationFailed(WorkerError):
    """Raised when the final verification gate rejects the change."""


class LLMError(WorkerError):
    """Raised when every configured LLM provider fails."""
