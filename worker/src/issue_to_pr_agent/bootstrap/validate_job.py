"""Sanity-validate a loaded Job before any repo work begins."""

from __future__ import annotations

from ..errors import BootstrapError
from ..job import Job


def validate_job(job: Job, *, installation_token: str) -> None:
    """Raise BootstrapError if the job is not actionable."""
    if not job.repo.owner or not job.repo.name:
        raise BootstrapError("job repo owner/name missing")
    if job.installation_id <= 0:
        raise BootstrapError("job installationId must be positive")
    if job.trigger == "issue_labeled" and job.issue_number is None:
        raise BootstrapError("issue_labeled job missing issueNumber")
    if job.trigger == "pr_comment" and job.pr_number is None:
        raise BootstrapError("pr_comment job missing prNumber")
    if not installation_token:
        raise BootstrapError("no installation token available")
