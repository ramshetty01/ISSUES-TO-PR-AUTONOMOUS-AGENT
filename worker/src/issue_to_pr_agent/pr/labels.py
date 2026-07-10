"""Outcome labels for the PR the agent opens.

Every agent PR is tagged so humans (and the dashboard) can filter automated
changes; the run outcome adds a state label on top. Application delegates to the
phase-19 github label helper.
"""

from __future__ import annotations

from ..github.client import GitHubClient
from ..github.labels import apply_labels
from ..job import Repo

# The marker label every agent PR carries.
AGENT_LABEL = "agent"

# Run state -> extra outcome label (kept in sync with RunState in shared-types).
_OUTCOME: dict[str, str] = {
    "succeeded": "automated-pr",
    "failed": "needs-attention",
    "refused": "safety-refused",
}


def outcome_labels(state: str, *, extra: list[str] | None = None) -> list[str]:
    """Labels for a PR given the run ``state`` (deduped, order-stable)."""
    labels = [AGENT_LABEL]
    mapped = _OUTCOME.get(state)
    if mapped:
        labels.append(mapped)
    for label in extra or []:
        if label not in labels:
            labels.append(label)
    return labels


def apply_outcome_labels(
    client: GitHubClient,
    repo: Repo,
    number: int,
    state: str,
    *,
    extra: list[str] | None = None,
) -> list[str]:
    """Compute and apply outcome labels to the PR/issue; return them."""
    labels = outcome_labels(state, extra=extra)
    apply_labels(client, repo, number, labels)
    return labels
