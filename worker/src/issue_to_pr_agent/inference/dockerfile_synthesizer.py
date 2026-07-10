"""Synthesize a build Dockerfile from RepoFacts using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .repo_facts import RepoFacts

TEMPLATES_DIR = Path(__file__).parent / "dockerfile_templates"


def select_template(facts: RepoFacts) -> str:
    """Choose the template filename for a set of facts."""
    lang, pm = facts.language, facts.package_manager
    if lang == "python":
        return "python.Dockerfile.j2"
    if lang == "node":
        return {
            "pnpm": "node-pnpm.Dockerfile.j2",
            "yarn": "node-yarn.Dockerfile.j2",
        }.get(pm, "node-npm.Dockerfile.j2")
    if lang == "go":
        return "go.Dockerfile.j2"
    if lang == "rust":
        return "rust.Dockerfile.j2"
    if lang == "java":
        return "java-maven.Dockerfile.j2" if pm == "maven" else "java-gradle.Dockerfile.j2"
    return "fallback.Dockerfile.j2"


def synthesize_dockerfile(facts: RepoFacts, templates_dir: Path = TEMPLATES_DIR) -> str:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template(select_template(facts))
    return template.render(
        language=facts.language,
        package_manager=facts.package_manager,
        framework=facts.framework or "",
        test_command=facts.test_command,
        coverage_command=facts.coverage_command or "",
    )
