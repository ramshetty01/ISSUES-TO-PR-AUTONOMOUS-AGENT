"""Derive a coverage command per stack (used by verification's coverage delta)."""

from __future__ import annotations

from .language_detector import Language

_NODE_COV = {
    "pnpm": "pnpm test -- --coverage",
    "yarn": "yarn test --coverage",
    "npm": "npm test -- --coverage",
}


def detect_coverage_command(language: Language, package_manager: str) -> str | None:
    if language == "python":
        return "pytest --cov --cov-report=xml"
    if language == "node":
        return _NODE_COV.get(package_manager, "npm test -- --coverage")
    if language == "go":
        return "go test -coverprofile=coverage.out ./..."
    if language == "rust":
        return None  # needs extra tooling (tarpaulin); skip by default
    if language == "java":
        return "mvn test" if package_manager == "maven" else "./gradlew test jacocoTestReport"
    return None
