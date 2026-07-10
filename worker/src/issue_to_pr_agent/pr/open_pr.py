"""Open the PR via the phase-19 github layer.

Resolves the base branch (repo default unless given), then delegates to
``github.pull_requests.open_pull``. Kept thin so the branch/base resolution is
what tests assert.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..github.client import GitHubClient
from ..github.pull_requests import open_pull
from ..job import Repo


@dataclass(slots=True)
class OpenedPR:
    number: int | None
    url: str | None
    base: str
    head: str


def open_pr(
    client: GitHubClient,
    repo: Repo,
    *,
    title: str,
    head: str,
    body: str,
    base: str | None = None,
) -> OpenedPR:
    """Create the PR from ``head`` into ``base`` (default branch if unset)."""
    if not head:
        raise ValueError("head branch is required to open a PR")
    resolved_base = base or client.get_default_branch(repo)
    if head == resolved_base:
        raise ValueError(f"head and base are the same branch ({head!r})")
    result = open_pull(client, repo, title=title, head=head, base=resolved_base, body=body)
    number = result.get("number")
    url = result.get("url")
    return OpenedPR(
        number=int(number) if isinstance(number, int) else None,
        url=str(url) if url else None,
        base=resolved_base,
        head=head,
    )
