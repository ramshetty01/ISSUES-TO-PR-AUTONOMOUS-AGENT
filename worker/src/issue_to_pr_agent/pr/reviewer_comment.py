"""Inline reviewer comments the agent leaves on its own PR.

Used to flag spots that merit a human's eye (heuristics, TODOs, risky edits).
Comment bodies are scrubbed, and posting delegates to the github review API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..github.client import GitHubClient
from ..job import Repo
from ..safety.log_scrubber import scrub


@dataclass(slots=True)
class ReviewComment:
    """One inline note anchored to a file and line in the diff."""

    path: str
    line: int
    body: str
    side: str = "RIGHT"  # "RIGHT" (new) | "LEFT" (old)

    def to_payload(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "side": self.side,
            "body": scrub(self.body),
        }


def build_review(
    comments: list[ReviewComment],
    *,
    body: str = "",
    event: str = "COMMENT",
) -> dict[str, Any]:
    """Shape a GitHub review payload (summary + inline comments), scrubbed."""
    payload: dict[str, Any] = {"event": event}
    if body:
        payload["body"] = scrub(body)
    if comments:
        payload["comments"] = [c.to_payload() for c in comments]
    return payload


def post_review(
    client: GitHubClient,
    repo: Repo,
    pull_number: int,
    comments: list[ReviewComment],
    *,
    body: str = "",
    event: str = "COMMENT",
) -> dict[str, Any]:
    """Post an inline review to the PR; no-op-safe when there's nothing to say."""
    if not comments and not body:
        return {}
    return client.create_review(
        repo,
        pull_number,
        body=scrub(body) if body else "",
        event=event,
        comments=[c.to_payload() for c in comments],
    )
