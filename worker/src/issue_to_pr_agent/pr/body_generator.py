"""Assemble the PR body from its parts.

Template-anchored to llm/prompts/pr_body.md: What / Why / Changes / Verification
/ Trace. Deterministic by default (an optional LLMClient may refine the one-line
summary). The whole body is scrubbed before return, so no secret can reach the
PR.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..llm.client import LLMClient
from ..llm.provider_base import Message
from ..safety.log_scrubber import scrub
from .diff_summary import summarize_diff
from .rationale import build_rationale
from .trace_link import trace_markdown


@dataclass(slots=True)
class PRBodyInput:
    """Everything needed to render a PR body."""

    issue_number: int | None
    issue_title: str = ""
    plan: str = ""
    diff: str = ""
    trace_id: str = ""
    langfuse_host: str = "http://localhost:3000"
    verification: str = ""
    coverage_delta: str = ""
    summary: str = ""


def _what(data: PRBodyInput, llm: LLMClient | None) -> str:
    if data.summary.strip():
        base = data.summary.strip()
    elif data.plan.strip():
        base = data.plan.strip().splitlines()[0].strip()
    elif data.issue_title.strip():
        base = f"Resolve: {data.issue_title.strip()}"
    else:
        base = "Automated change produced by the issue-to-PR agent."
    if llm is not None and not data.summary.strip():
        try:
            prompt = (
                "In one factual sentence, summarise the change that fixes issue "
                f"#{data.issue_number} ({data.issue_title!r}). No secrets."
            )
            out = llm.complete([Message(role="user", content=prompt)], max_tokens=64).text.strip()
            if out:
                base = out.splitlines()[0].strip()
        except Exception:  # best-effort refinement
            pass
    return base


def generate_body(data: PRBodyInput, *, llm: LLMClient | None = None) -> str:
    """Render the full PR body (markdown), scrubbed of secrets."""
    changes = summarize_diff(data.diff).to_markdown()
    rationale = build_rationale(
        issue_number=data.issue_number,
        issue_title=data.issue_title,
        plan=data.plan,
    )
    verification = data.verification.strip() or "_No verification recorded._"
    if data.coverage_delta.strip():
        verification = f"{verification}\n\nCoverage: {data.coverage_delta.strip()}"

    body = "\n".join(
        [
            "## What",
            "",
            _what(data, llm),
            "",
            "## Why",
            "",
            rationale,
            "",
            "## Changes",
            "",
            changes,
            "",
            "## Verification",
            "",
            verification,
            "",
            "## Trace",
            "",
            trace_markdown(data.langfuse_host, data.trace_id),
            "",
            "---",
            "🤖 Opened automatically by the issue-to-PR agent.",
        ]
    )
    return scrub(body)
