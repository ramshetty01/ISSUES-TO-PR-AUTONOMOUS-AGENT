"""Post progress/result comments."""

from __future__ import annotations

from ..job import Repo
from .client import GitHubClient


def post_comment(client: GitHubClient, repo: Repo, issue_number: int, body: str) -> str:
    data = client.create_comment(repo, issue_number, body)
    return str(data.get("html_url", ""))
