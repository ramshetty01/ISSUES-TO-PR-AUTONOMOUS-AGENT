"""Derive the test command from language + package manager + framework."""

from __future__ import annotations

from .language_detector import Language

_NODE_RUN = {"pnpm": "pnpm test", "yarn": "yarn test", "npm": "npm test"}


def detect_test_command(
    language: Language, package_manager: str, framework: str | None
) -> str:
    if language == "python":
        return "pytest" if (framework in (None, "pytest")) else f"python -m {framework}"
    if language == "node":
        return _NODE_RUN.get(package_manager, "npm test")
    if language == "go":
        return "go test ./..."
    if language == "rust":
        return "cargo test"
    if language == "java":
        return "mvn test" if package_manager == "maven" else "./gradlew test"
    return "true"  # unknown: no-op so the pipeline can still proceed
