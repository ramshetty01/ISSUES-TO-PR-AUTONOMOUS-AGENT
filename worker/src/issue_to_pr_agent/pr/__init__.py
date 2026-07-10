"""PR authoring: turn a verified diff into a high-quality pull request."""

from .body_generator import PRBodyInput, generate_body
from .diff_summary import DiffSummary, FileChange, summarize_diff
from .labels import AGENT_LABEL, apply_outcome_labels, outcome_labels
from .open_pr import OpenedPR, open_pr
from .rationale import build_rationale, closes_line
from .reviewer_comment import ReviewComment, build_review, post_review
from .title_generator import generate_title
from .trace_link import trace_markdown, trace_url

__all__ = [
    "PRBodyInput",
    "generate_body",
    "DiffSummary",
    "FileChange",
    "summarize_diff",
    "AGENT_LABEL",
    "apply_outcome_labels",
    "outcome_labels",
    "OpenedPR",
    "open_pr",
    "build_rationale",
    "closes_line",
    "ReviewComment",
    "build_review",
    "post_review",
    "generate_title",
    "trace_markdown",
    "trace_url",
]
