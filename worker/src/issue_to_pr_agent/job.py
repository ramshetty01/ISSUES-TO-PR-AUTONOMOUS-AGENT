"""The Job model — the worker side of the contract produced by github-app.

Kept in sync with packages/shared-types/src/job.ts. The JSON on the wire uses
camelCase (installationId, issueNumber, headSha, createdAt); this model accepts
both camelCase (via aliases) and snake_case (populate_by_name).
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from .errors import BootstrapError

TriggerKind = Literal["issue_labeled", "pr_comment"]


class _CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Repo(_CamelModel):
    owner: str
    name: str


class Job(_CamelModel):
    id: str
    repo: Repo
    installation_id: int
    trigger: TriggerKind
    head_sha: str = ""
    labels: list[str] = []
    created_at: str = ""
    issue_number: int | None = None
    issue_title: str = ""
    issue_body: str = ""
    pr_number: int | None = None

    @classmethod
    def from_json(cls, raw: str) -> "Job":
        """Parse a Job from a JSON string, raising BootstrapError on failure."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:  # pragma: no cover - trivial
            raise BootstrapError(f"job is not valid JSON: {exc}") from exc
        try:
            return cls.model_validate(data)
        except Exception as exc:  # pydantic ValidationError
            raise BootstrapError(f"job failed validation: {exc}") from exc
