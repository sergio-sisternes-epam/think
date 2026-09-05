#!/usr/bin/env python3
"""Audit every tracked source file with bounded APM subprocess concurrency."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AuditResult:
    path: str
    returncode: int
    output: str


def tracked_files(root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return sorted(
        path.decode("utf-8")
        for path in result.stdout.split(b"\0")
        if path and (root / path.decode("utf-8")).is_file()
    )


def audit_file(path: str, root: Path = ROOT) -> AuditResult:
    result = subprocess.run(
        ["apm", "audit", "--file", path],
        cwd=root,
        capture_output=True,
        text=True,
    )
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    return AuditResult(path, result.returncode, output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(4, os.cpu_count() or 1),
        help="Maximum concurrent APM audit processes",
    )
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    files = tracked_files()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        results = list(executor.map(audit_file, files))

    failures = [result for result in results if result.returncode != 0]
    for result in failures:
        print(f"::error file={result.path}::APM source audit failed")
        if result.output:
            print(result.output)

    print(f"source_audit_files={len(files)}")
    print(f"source_audit_failures={len(failures)}")
    if failures:
        print("source_audit=failed")
        return 1
    print("source_audit=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
