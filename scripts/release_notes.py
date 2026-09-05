#!/usr/bin/env python3
"""Extract one curated release section from CHANGELOG.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from release_readiness import ROOT, SEMVER


def release_notes(version: str, root: Path = ROOT) -> str:
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"(?ms)^## \[{re.escape(version)}\]"
        rf"(?: - [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}})?\s*"
        rf"(?P<body>.*?)(?=^## \[|^\[[^\]]+\]:|\Z)",
        changelog,
    )
    if not match:
        raise ValueError(f"CHANGELOG.md: release notes not found for {version}")
    notes = match.group("body").strip()
    first_section = notes.find("### ")
    if first_section >= 0:
        notes = notes[first_section:]
    if not notes:
        raise ValueError(f"CHANGELOG.md: release notes are empty for {version}")
    return notes


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if not re.fullmatch(SEMVER, args.version):
        parser.error(f"invalid semantic version: {args.version}")

    args.output.write_text(f"{release_notes(args.version, root)}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
