#!/usr/bin/env python3
"""Audit every tracked source file with bounded APM subprocess concurrency."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from ci_output import emit_error, print_summary, write_github_outputs
from command_runner import CommandError, run_command


ROOT = Path(__file__).resolve().parents[1]
GIT_TIMEOUT_SECONDS = 120
AUDIT_TIMEOUT_SECONDS = 300


class SourceAuditError(RuntimeError):
    """Raised when the authoritative source set cannot be audited."""


@dataclass(frozen=True)
class AuditResult:
    path: str
    returncode: int
    output: str


def tracked_files(root: Path = ROOT) -> list[str]:
    try:
        result = run_command(
            ["git", "ls-files", "--cached", "-z"],
            cwd=root,
            timeout=GIT_TIMEOUT_SECONDS,
            label="git source enumeration",
        )
    except CommandError as error:
        raise SourceAuditError(str(error)) from error

    root = root.resolve()
    files = []
    for path in result.stdout.split("\0"):
        if not path:
            continue
        candidate = root / path
        if candidate.is_symlink():
            raise SourceAuditError(f"{path}: tracked symbolic links are not auditable")
        try:
            candidate.resolve().relative_to(root)
        except ValueError as error:
            raise SourceAuditError(f"{path}: tracked path escapes the repository") from error
        if candidate.is_file():
            files.append(path)
    return sorted(files)


def audit_file(
    path: str,
    root: Path = ROOT,
    timeout: int = AUDIT_TIMEOUT_SECONDS,
) -> AuditResult:
    try:
        result = run_command(
            ["apm", "audit", "--file", path],
            cwd=root,
            timeout=timeout,
            label=f"APM source audit for {path}",
            check=False,
        )
    except CommandError as error:
        return AuditResult(path, 124, str(error))
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    return AuditResult(path, result.returncode, output)


def report_results(
    results: list[AuditResult],
    github_output: Path | None = None,
) -> int:
    failures = [result for result in results if result.returncode != 0]
    for result in failures:
        diagnostic = result.output.splitlines()[0] if result.output else "no diagnostic"
        emit_error(
            f"APM source audit failed: {diagnostic}",
            title="APM source audit failed",
            file=result.path,
        )
        if result.output:
            print(result.output)

    fields = {
        "source_audit_files": len(results),
        "source_audit_failures": len(failures),
        "source_audit": "failed" if failures else "pass",
    }
    print_summary(fields)
    write_github_outputs(github_output, fields)
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(8, os.cpu_count() or 1),
        help="Maximum concurrent APM audit processes",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file",
    )
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    try:
        files = tracked_files()
    except SourceAuditError as error:
        emit_error(str(error), title="Source enumeration failed")
        write_github_outputs(
            args.github_output,
            {
                "source_audit_files": 0,
                "source_audit_failures": 1,
                "source_audit": "failed",
            },
        )
        return 1

    worker = partial(audit_file, root=ROOT)
    max_workers = min(args.jobs, len(files)) if files else 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(worker, files))
    return report_results(results, args.github_output)


if __name__ == "__main__":
    raise SystemExit(main())
