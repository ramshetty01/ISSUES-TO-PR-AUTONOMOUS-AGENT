"""Phase 21 Dockerfile synthesis tests (template selection + render + build)."""

from __future__ import annotations

from pathlib import Path

from issue_to_pr_agent.inference.repo_facts import RepoFacts, detect_repo_facts
from issue_to_pr_agent.inference.dockerfile_synthesizer import (
    select_template,
    synthesize_dockerfile,
)
from issue_to_pr_agent.inference.docker_build import build_image
from issue_to_pr_agent.sandbox.command_runner import CommandResult


def facts(**over: object) -> RepoFacts:
    base = dict(
        language="python",
        package_manager="pip",
        framework="pytest",
        test_command="pytest",
        coverage_command="pytest --cov",
    )
    base.update(over)
    return RepoFacts(**base)  # type: ignore[arg-type]


def test_template_selection() -> None:
    assert select_template(facts()) == "python.Dockerfile.j2"
    assert select_template(facts(language="node", package_manager="pnpm")) == "node-pnpm.Dockerfile.j2"
    assert select_template(facts(language="node", package_manager="yarn")) == "node-yarn.Dockerfile.j2"
    assert select_template(facts(language="node", package_manager="npm")) == "node-npm.Dockerfile.j2"
    assert select_template(facts(language="go", package_manager="go")) == "go.Dockerfile.j2"
    assert select_template(facts(language="rust", package_manager="cargo")) == "rust.Dockerfile.j2"
    assert select_template(facts(language="java", package_manager="maven")) == "java-maven.Dockerfile.j2"
    assert select_template(facts(language="java", package_manager="gradle")) == "java-gradle.Dockerfile.j2"
    assert select_template(facts(language="unknown", package_manager="unknown")) == "fallback.Dockerfile.j2"


def test_python_render_embeds_test_command() -> None:
    out = synthesize_dockerfile(facts(test_command="pytest -q"))
    assert "FROM python:3.12-slim" in out
    assert "pytest -q" in out


def test_python_uv_render_uses_uv() -> None:
    out = synthesize_dockerfile(facts(package_manager="uv"))
    assert "uv" in out


def test_pnpm_render() -> None:
    out = synthesize_dockerfile(facts(language="node", package_manager="pnpm", test_command="pnpm test"))
    assert "corepack enable" in out
    assert "pnpm test" in out


def test_end_to_end_facts_to_dockerfile(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    f = detect_repo_facts(tmp_path)
    assert f.language == "python"
    dockerfile = synthesize_dockerfile(f)
    assert "python" in dockerfile.lower()


def test_build_image_writes_dockerfile_and_reports(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_runner(argv: list[str], cwd: Path) -> CommandResult:
        calls.append(argv)
        return CommandResult(0, "Successfully built", "")

    res = build_image("FROM scratch\n", tmp_path, "itpr-build:test", runner=fake_runner)
    assert res.success is True
    assert (tmp_path / "Dockerfile.itpr").read_text() == "FROM scratch\n"
    assert calls[0][:3] == ["docker", "build", "-f"]


def test_build_image_captures_failure(tmp_path: Path) -> None:
    def fake_runner(argv: list[str], cwd: Path) -> CommandResult:
        return CommandResult(1, "", "error: step failed")

    res = build_image("FROM bad\n", tmp_path, "itpr:bad", runner=fake_runner)
    assert res.success is False
    assert "step failed" in res.logs
