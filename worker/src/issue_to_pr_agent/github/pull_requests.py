"""Open pull requests."""

from __future__ import annotations

from ..job import Repo
from .client import GitHubClient


def open_pull(
    client: GitHubClient, repo: Repo, *, title: str, head: str, base: str, body: str
) -> dict[str, object]:
    data = client.create_pull(repo, title=title, head=head, base=base, body=body)
    return {"number": data.get("number"), "url": data.get("html_url")}
