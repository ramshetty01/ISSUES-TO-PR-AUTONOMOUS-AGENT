"""Apply labels to an issue/PR."""

from __future__ import annotations

from ..job import Repo
from .client import GitHubClient


def apply_labels(
    client: GitHubClient, repo: Repo, issue_number: int, labels: list[str]
) -> None:
    if not labels:
        return
    client.add_labels(repo, issue_number, labels)
