"""Branch-protection awareness: read protection + guard against protected pushes."""

from __future__ import annotations

from ..errors import SafetyRefusal
from ..job import Repo
from .client import GitHubClient


def is_protected(client: GitHubClient, repo: Repo, branch: str) -> bool:
    return client.get_branch_protection(repo, branch) is not None


def assert_not_protected(branch: str, protected: set[str]) -> None:
    """Raise SafetyRefusal if `branch` is in the protected set."""
    if branch in protected:
        raise SafetyRefusal(
            "workflow_write_blocked",
            f"'{branch}' is protected; changes must go through a PR branch",
        )
