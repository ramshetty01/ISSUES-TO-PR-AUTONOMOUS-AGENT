"""Parse coverage.py XML (Cobertura format) into a Coverage summary."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .coverage import Coverage


def parse_coverage_py(xml: str) -> Coverage:
    root = ET.fromstring(xml)
    line_rate = float(root.get("line-rate", 0.0))
    per_file: dict[str, float] = {}
    covered = total = 0
    for cls in root.findall(".//class"):
        lines = cls.findall(".//line")
        c = sum(1 for ln in lines if int(ln.get("hits", 0)) > 0)
        t = len(lines)
        covered += c
        total += t
        if t:
            per_file[cls.get("filename", "?")] = round(100.0 * c / t, 2)
    return Coverage(
        percent=round(line_rate * 100.0, 2),
        covered_lines=covered,
        total_lines=total,
        per_file=per_file,
    )
