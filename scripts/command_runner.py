#!/usr/bin/env python3
"""Run bounded external commands with consistent diagnostics."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


class CommandError(RuntimeError):
    """Raised when an external command fails or exceeds its time limit."""


def run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
    label: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise CommandError(f"{label} timed out after {timeout}s") from error
    except subprocess.CalledProcessError as error:
        diagnostic = error.stderr.strip() or error.stdout.strip()
        detail = f": {diagnostic}" if diagnostic else ""
        raise CommandError(
            f"{label} failed with exit code {error.returncode}{detail}"
        ) from error


def run_git(
    *args: str,
    cwd: Path,
    timeout: int,
) -> str:
    result = run_command(
        ["git", *args],
        cwd=cwd,
        timeout=timeout,
        label=f"git {' '.join(args)}",
    )
    return result.stdout.strip()
