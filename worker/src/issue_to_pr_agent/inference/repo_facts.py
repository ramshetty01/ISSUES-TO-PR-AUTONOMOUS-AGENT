"""Aggregate detections into a single RepoFacts object."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .coverage_detector import detect_coverage_command
from .framework_detector import detect_framework
from .language_detector import Language, detect_language
from .package_manager_detector import detect_package_manager
from .test_command_detector import detect_test_command


@dataclass(slots=True)
class RepoFacts:
    language: Language
    package_manager: str
    framework: str | None
    test_command: str
    coverage_command: str | None


def detect_repo_facts(repo_dir: Path) -> RepoFacts:
    language = detect_language(repo_dir)
    package_manager = detect_package_manager(repo_dir, language)
    framework = detect_framework(repo_dir, language)
    return RepoFacts(
        language=language,
        package_manager=package_manager,
        framework=framework,
        test_command=detect_test_command(language, package_manager, framework),
        coverage_command=detect_coverage_command(language, package_manager),
    )
