"""Build the "Why" of a PR — the rationale tied to the originating issue.

Keeps the change explainable and always emits a ``Closes #N`` link so merging
the PR closes the issue that triggered the run.
"""

from __future__ import annotations


def closes_line(issue_number: int | None) -> str:
    """The GitHub auto-close reference, or an empty string when unknown."""
    return f"Closes #{issue_number}" if issue_number else ""


def build_rationale(
    *,
    issue_number: int | None,
    issue_title: str = "",
    plan: str = "",
) -> str:
    """Assemble the rationale text linking the change back to the issue."""
    parts: list[str] = []
    close = closes_line(issue_number)
    if close and issue_title:
        parts.append(f"{close} — {issue_title.strip()}.")
    elif close:
        parts.append(f"{close}.")
    elif issue_title:
        parts.append(f"{issue_title.strip()}.")
    plan = plan.strip()
    if plan:
        first = plan.splitlines()[0].strip()
        parts.append(f"Approach: {first}")
    if not parts:
        parts.append("Automated change produced by the issue-to-PR agent.")
    return " ".join(parts)
