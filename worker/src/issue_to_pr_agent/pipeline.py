"""End-to-end run pipeline: the orchestration that ties every worker subsystem
together.

Stages: context (repo map) -> agent loop -> safety gate -> verification ->
PR authoring -> observability + storage. Each external collaborator (sandbox,
LLM, GitHub, storage) is injected, and every outward-facing stage degrades
gracefully — a missing GitHub token skips PR authoring, an unreachable Langfuse
skips ingestion — so a run never crashes purely because an optional dependency
is absent. This is what ``main.run`` invokes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent import run_agent
from .errors import SafetyRefusal, SandboxError
from .llm.client import LLMClient
from .llm.provider_base import TokenUsage
from .observability import (
    ArtifactWriter,
    CostReport,
    EventLog,
    LangfuseClient,
    RunSummary,
    Tracer,
    build_redacted_archive,
    build_run_summary,
)
from .repo_map import build_context_pack
from .runtime_context import RuntimeContext
from .safety import SafetyGuard, load_safety_policy
from .sandbox.base import Sandbox
from .tools.registry import ToolContext, build_default_registry
from .verification import (
    check_diff_size,
    check_forbidden_diff,
    final_gate,
    load_forbidden_paths,
)
from .verification.ci_runner import run_tests
from .verification.test_result import TestResult


@dataclass(slots=True)
class PipelineResult:
    summary: RunSummary
    exit_code: int
    pr_url: str | None = None


def _policies_dir() -> Path:
    return Path(os.environ.get("ITPR_POLICIES_DIR", "policies"))


def _load_guard() -> SafetyGuard:
    pol_dir = _policies_dir()
    if pol_dir.is_dir():
        try:
            return SafetyGuard(load_safety_policy(pol_dir))
        except Exception:  # fall back to built-in safe defaults
            pass
    return SafetyGuard()


def _issue_text(ctx: RuntimeContext, override: str | None) -> str:
    if override:
        return override
    env = os.environ.get("ITPR_ISSUE_BODY")
    if env:
        return env
    num = ctx.job.issue_number or ctx.job.pr_number
    return f"Resolve issue #{num} in {ctx.job.repo.owner}/{ctx.job.repo.name}."


def run_pipeline(
    ctx: RuntimeContext,
    *,
    sandbox: Sandbox,
    llm: LLMClient,
    github: Any | None = None,
    storage: Any | None = None,
    tracer: Tracer | None = None,
    issue_text: str | None = None,
    test_command: str | None = None,
) -> PipelineResult:
    tracer = tracer or Tracer(ctx.run_id)
    events = EventLog()
    cost = CostReport()
    guard = _load_guard()
    langfuse = LangfuseClient(ctx.config.langfuse_host)
    started_at = tracer._clock()  # same clock the tracer stamps spans with

    state = "running"
    refusal: dict[str, Any] | None = None
    pr_url: str | None = None
    diff = ""

    events.record("start", f"run {ctx.run_id} for {ctx.job.repo.owner}/{ctx.job.repo.name}")

    from .github.clone import SubprocessGitRunner

    git_runner = SubprocessGitRunner()
    pr_branch: str | None = None
    if github is not None:
        pr_branch = _prepare_pr_branch(ctx, git_runner, events)

    with tracer.span("sandbox_start"):
        sandbox.start()

    try:
        issue = _issue_text(ctx, issue_text)

        # --- context ------------------------------------------------------
        context = ""
        with tracer.span("build_context"):
            try:
                context = build_context_pack(ctx.workspace, issue).text
                events.record("context", f"packed {len(context)} chars of repo context")
            except Exception as exc:  # context is best-effort
                events.record("context", f"context pack skipped: {exc}")

        # --- agent loop ---------------------------------------------------
        with tracer.span("agent_loop") as span:
            registry = build_default_registry()
            toolctx = ToolContext(
                sandbox=sandbox,
                repo_dir=ctx.workspace,
                git=git_runner,
                github=github,
                repo=ctx.job.repo,
            )
            result = run_agent(llm, registry, toolctx, issue, context=context)
            diff = result.diff
            span.attributes.update(turns=result.turns, success=result.success)
            events.record(
                "agent", f"agent finished: {result.stop_reason} ({result.turns} turns)"
            )

        cost.record(
            _provider_name(llm),
            TokenUsage(input=llm.tokens.input, output=llm.tokens.output),
        )

        # --- safety gate --------------------------------------------------
        with tracer.span("safety_gate"):
            try:
                guard.guard_commit_diff(diff)
                events.record("safety", "diff cleared the safety gate")
            except SafetyRefusal as exc:
                state = "refused"
                refusal = {"reason": exc.reason, "message": str(exc)}
                events.record("refuse", f"safety refusal: {exc.reason}")

        # --- verification -------------------------------------------------
        verdict_ok = False
        if state != "refused":
            with tracer.span("verification"):
                tests = _run_tests_safe(sandbox, test_command, events)
                forbidden = check_forbidden_diff(diff, _forbidden_paths())
                size = check_diff_size(diff)
                verdict = final_gate(tests=tests, forbidden=forbidden, diff_size=size)
                verdict_ok = verdict.passed
                events.record(
                    "verify",
                    "verification " + ("passed" if verdict_ok else "failed: " + _reasons(verdict)),
                )
                state = "succeeded" if verdict_ok else "failed"

        # --- PR authoring -------------------------------------------------
        if state == "succeeded" and github is not None and diff.strip():
            with tracer.span("pr_authoring"):
                pr_url = _open_pr_safe(
                    ctx,
                    github,
                    diff,
                    result.summary,
                    langfuse,
                    events,
                    branch=pr_branch,
                    git_runner=git_runner,
                )
        elif state == "succeeded" and github is None:
            events.record("pr", "PR authoring skipped (no GitHub client)")
        elif state == "succeeded":
            events.record("pr", "PR authoring skipped (empty diff)")

    finally:
        with tracer.span("sandbox_teardown"):
            try:
                sandbox.teardown()
            except Exception:  # teardown is best-effort
                pass

    if state == "running":
        state = "succeeded"

    summary = build_run_summary(
        run_id=ctx.run_id,
        job=ctx.job,
        state=state,
        started_at=started_at,
        finished_at=tracer._clock(),
        timeline=events.to_timeline(),
        usage=cost.usage,
        dollars=cost.dollars,
        refusal=refusal,
        pr_url=pr_url,
        trace_url=langfuse.trace_url(ctx.run_id),
    )

    _persist(ctx, summary, tracer, cost, events, storage, langfuse)

    exit_code = 0 if state in ("succeeded", "refused") else 1
    return PipelineResult(summary=summary, exit_code=exit_code, pr_url=pr_url)


# --- helpers ---------------------------------------------------------------


def _provider_name(llm: LLMClient) -> str:
    try:
        return llm._router._providers[0].name
    except Exception:
        return "mock"


def _forbidden_paths() -> list[str]:
    path = _policies_dir() / "forbidden-paths.yaml"
    try:
        return load_forbidden_paths(path)
    except Exception:
        return [".github/workflows/", ".git/", ".env", "secrets/"]


def _run_tests_safe(sandbox: Sandbox, command: str | None, events: EventLog) -> TestResult:
    if not command:
        events.record("test", "no test command detected; skipping test run")
        return TestResult()  # no failures/errors -> ok, but nothing asserted
    try:
        result = run_tests(sandbox, command)
        events.record("test", f"tests: {result.passed} passed, {result.failed} failed")
        return result
    except Exception as exc:
        events.record("test", f"test run errored: {exc}")
        return TestResult(errors=1)


def _reasons(verdict: Any) -> str:
    return ", ".join(k for k, ok in verdict.checks.items() if not ok)


def _open_pr_safe(
    ctx: RuntimeContext,
    github: Any,
    diff: str,
    summary: str,
    langfuse: LangfuseClient,
    events: EventLog,
    *,
    branch: str | None,
    git_runner: Any | None,
) -> str | None:
    from .pr import PRBodyInput, apply_outcome_labels, generate_body, generate_title, open_pr

    try:
        if not branch or git_runner is None:
            events.record("pr", "PR authoring skipped (no PR branch prepared)")
            return None
        issue_number = ctx.job.issue_number
        title = generate_title(issue_title=summary, issue_number=issue_number)
        body = generate_body(
            PRBodyInput(
                issue_number=issue_number,
                issue_title=summary,
                diff=diff,
                trace_id=ctx.run_id,
                langfuse_host=ctx.config.langfuse_host,
                verification="Verification passed.",
            )
        )
        _commit_and_push_pr_branch(ctx, git_runner, branch, issue_number, events)
        opened = open_pr(github, ctx.job.repo, title=title, head=branch, body=body)
        if opened.number is not None:
            apply_outcome_labels(github, ctx.job.repo, opened.number, "succeeded")
        events.record("pr_opened", f"opened PR {opened.url}", {"url": opened.url})
        return opened.url
    except Exception as exc:  # PR authoring is best-effort at the boundary
        events.record("pr", f"PR authoring failed: {exc}")
        return None


def _prepare_pr_branch(ctx: RuntimeContext, git_runner: Any, events: EventLog) -> str:
    """Ensure the workspace is a checkout and move edits onto a PR branch."""
    from .github.branches import create_branch
    from .github.clone import clone_repo

    if not (ctx.workspace / ".git").exists():
        token = ctx.config.github_installation_token
        if not token:
            raise SandboxError("cannot clone repo without a GitHub installation token")
        clone_repo(git_runner, ctx.job.repo, token, ctx.workspace, depth=None)
        events.record("git", "cloned target repository")

    branch = f"agent/{ctx.run_id}"
    res = git_runner.run(["rev-parse", "--verify", branch], cwd=ctx.workspace)
    if res.returncode == 0:
        checkout = git_runner.run(["checkout", branch], cwd=ctx.workspace)
        if checkout.returncode != 0:
            raise SandboxError(f"cannot checkout existing branch {branch}")
    else:
        create_branch(git_runner, ctx.workspace, branch)
    events.record("git", f"using PR branch {branch}")
    return branch


def _commit_and_push_pr_branch(
    ctx: RuntimeContext,
    git_runner: Any,
    branch: str,
    issue_number: int | None,
    events: EventLog,
) -> None:
    from .github.branches import push_branch
    from .github.commits import commit_all

    message = (
        f"fix: address issue #{issue_number}"
        if issue_number is not None
        else f"fix: apply agent changes for {ctx.run_id}"
    )
    sha = commit_all(git_runner, ctx.workspace, message)
    events.record("git", f"committed {sha[:12]}")
    push_branch(git_runner, ctx.workspace, branch, protected={"main", "master"})
    events.record("git", f"pushed PR branch {branch}")


def _persist(
    ctx: RuntimeContext,
    summary: RunSummary,
    tracer: Tracer,
    cost: CostReport,
    events: EventLog,
    storage: Any | None,
    langfuse: LangfuseClient,
) -> None:
    trace = tracer.export()
    artifacts = {
        "summary.json": summary.to_dict(),
        "trace.json": trace,
        "events.json": events.to_timeline(),
        "cost.json": cost.to_dict(),
    }
    # Local artifacts, redaction-scrubbed.
    try:
        writer = ArtifactWriter(ctx.workspace / ".itpr" / ctx.run_id)
        for name, obj in artifacts.items():
            writer.write_json(name, obj)
        build_redacted_archive(ctx.workspace / ".itpr" / f"{ctx.run_id}.tar.gz", artifacts)
    except Exception:  # persistence is best-effort
        pass
    # Object storage (S3/LocalStack, else local fallback), when wired.
    if storage is not None:
        try:
            from .storage import RunArtifacts, TraceArchive

            ra = RunArtifacts(storage, ctx.run_id)
            for name, obj in artifacts.items():
                ra.put_json(name, obj)
            TraceArchive(storage).archive_trace(ctx.run_id, trace)
        except Exception:
            pass
    # Self-hosted Langfuse trace ingestion (no-op without credentials).
    try:
        langfuse.ingest(trace)
    except Exception:
        pass
