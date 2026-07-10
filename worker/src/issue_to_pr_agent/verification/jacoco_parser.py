"""Parse JaCoCo XML (Java coverage) into a Coverage summary."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .coverage import Coverage


def parse_jacoco(xml: str) -> Coverage:
    root = ET.fromstring(xml)
    covered = missed = 0
    for counter in root.findall("counter"):
        if counter.get("type") == "LINE":
            covered = int(counter.get("covered", 0))
            missed = int(counter.get("missed", 0))
    total = covered + missed
    percent = round(100.0 * covered / total, 2) if total else 0.0
    return Coverage(percent=percent, covered_lines=covered, total_lines=total)
