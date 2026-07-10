"""Run a style/lint command inside the sandbox."""

from __future__ import annotations

from dataclasses import dataclass

from ..sandbox.base import Sandbox


@dataclass(slots=True)
class StyleResult:
    ok: bool
    output: str


def run_style_check(sandbox: Sandbox, command: str, *, timeout: float | None = 300) -> StyleResult:
    res = sandbox.exec(["sh", "-c", command], timeout=timeout)
    return StyleResult(ok=res.exit_code == 0 and not res.timed_out, output=(res.stdout + res.stderr).strip())
