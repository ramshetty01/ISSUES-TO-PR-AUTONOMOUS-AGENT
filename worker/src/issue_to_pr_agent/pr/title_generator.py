"""Generate the PR title.

LLM-assisted but template-anchored: an optional ``LLMClient`` may refine the
title, but a deterministic fallback derived from the issue always works (and is
what tests exercise). The result is scrubbed and length-capped.
"""

from __future__ import annotations

from ..llm.client import LLMClient
from ..llm.provider_base import Message
from ..safety.log_scrubber import scrub

MAX_TITLE = 72


def _fallback_title(issue_title: str, issue_number: int | None) -> str:
    base = issue_title.strip() or "Automated fix"
    if not base.lower().startswith(("fix", "add", "update", "refactor", "chore")):
        base = f"Fix: {base}"
    suffix = f" (#{issue_number})" if issue_number else ""
    return _truncate(base, MAX_TITLE - len(suffix)) + suffix


def _truncate(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: max(0, limit - 1)].rstrip() + "…"


def generate_title(
    *,
    issue_title: str,
    issue_number: int | None,
    llm: LLMClient | None = None,
) -> str:
    """Produce a concise, scrubbed PR title; fall back to a template."""
    title = _fallback_title(issue_title, issue_number)
    if llm is not None:
        try:
            prompt = (
                "Write a concise (<72 char), imperative pull-request title for the "
                f"change fixing issue #{issue_number}: {issue_title!r}. "
                "Return only the title, no quotes."
            )
            out = llm.complete(
                [Message(role="user", content=prompt)], max_tokens=32
            ).text.strip().splitlines()
            if out and out[0].strip():
                suffix = f" (#{issue_number})" if issue_number else ""
                title = _truncate(out[0].strip(), MAX_TITLE - len(suffix)) + suffix
        except Exception:  # LLM is best-effort; template already set
            pass
    return scrub(title)
