"""Operator-UX score: does the run summary give an operator what they need?"""

from __future__ import annotations


def operator_ux_score(run_summary: dict) -> float:
    checks = [
        bool(run_summary.get("traceUrl")),
        bool(run_summary.get("timeline")),
        bool(run_summary.get("prUrl")) or run_summary.get("state") == "refused",
        "dollars" in run_summary,
        bool(run_summary.get("state")),
    ]
    return round(sum(1 for c in checks if c) / len(checks), 4)
