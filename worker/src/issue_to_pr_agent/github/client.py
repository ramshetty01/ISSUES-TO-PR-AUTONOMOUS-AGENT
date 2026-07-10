"""Authenticated GitHub REST client with an injectable transport.

The transport is a callable so tests can supply a fake and exercise the client
without network access. The default transport uses urllib.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable

from ..errors import WorkerError
from ..job import Repo

API = "https://api.github.com"

# (method, url, headers, body_bytes) -> (status, parsed_json)
Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, Any]]


def default_transport(
    method: str, url: str, headers: dict[str, str], body: bytes | None
) -> tuple[int, Any]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310 - https api only
            payload = resp.read()
            return resp.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as exc:  # type: ignore[attr-defined]
        payload = exc.read()
        return exc.code, (json.loads(payload) if payload else None)


class GitHubClient:
    def __init__(self, token: str, transport: Transport = default_transport) -> None:
        self._token = token
        self._transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "issue-to-pr-agent",
            "Content-Type": "application/json",
        }

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        return self._transport(method, f"{API}{path}", self._headers(), data)

    def get_default_branch(self, repo: Repo) -> str:
        status, data = self._request("GET", f"/repos/{repo.owner}/{repo.name}")
        if status != 200:
            raise WorkerError(f"repo fetch failed ({status})")
        return str(data["default_branch"])

    def create_pull(
        self, repo: Repo, *, title: str, head: str, base: str, body: str
    ) -> dict[str, Any]:
        status, data = self._request(
            "POST",
            f"/repos/{repo.owner}/{repo.name}/pulls",
            {"title": title, "head": head, "base": base, "body": body},
        )
        if status not in (200, 201):
            raise WorkerError(f"create pull failed ({status})")
        return data

    def add_labels(self, repo: Repo, issue_number: int, labels: list[str]) -> None:
        status, _ = self._request(
            "POST",
            f"/repos/{repo.owner}/{repo.name}/issues/{issue_number}/labels",
            {"labels": labels},
        )
        if status not in (200, 201):
            raise WorkerError(f"add labels failed ({status})")

    def create_comment(self, repo: Repo, issue_number: int, body: str) -> dict[str, Any]:
        status, data = self._request(
            "POST",
            f"/repos/{repo.owner}/{repo.name}/issues/{issue_number}/comments",
            {"body": body},
        )
        if status not in (200, 201):
            raise WorkerError(f"create comment failed ({status})")
        return data

    def get_branch_protection(self, repo: Repo, branch: str) -> dict[str, Any] | None:
        status, data = self._request(
            "GET", f"/repos/{repo.owner}/{repo.name}/branches/{branch}/protection"
        )
        if status == 404:
            return None
        if status != 200:
            raise WorkerError(f"branch protection fetch failed ({status})")
        return data
