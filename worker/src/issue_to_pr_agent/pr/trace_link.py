"""Build a link into the self-hosted Langfuse trace for a run.

Mirrors ``observability.LangfuseClient.trace_url`` so the PR body and the run
summary point at the same URL, without importing the client (a bare host +
trace id is all that is needed here).
"""

from __future__ import annotations


def trace_url(langfuse_host: str, trace_id: str) -> str:
    """Deep-link to the Langfuse trace (matches LangfuseClient.trace_url)."""
    return f"{langfuse_host.rstrip('/')}/trace/{trace_id}"


def trace_markdown(langfuse_host: str, trace_id: str) -> str:
    """A markdown link for the PR body's "Trace" section."""
    if not trace_id:
        return "_No trace recorded for this run._"
    return f"[Langfuse trace `{trace_id}`]({trace_url(langfuse_host, trace_id)})"
