#!/usr/bin/env python3
"""Run bounded external commands with consistent diagnostics."""

from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path


MAX_CAPTURE_BYTES = 65536


class CommandError(RuntimeError):
    """Raised when an external command fails or exceeds its time limit."""


def github_git_auth_environment(token: str | None) -> dict[str, str] | None:
    if not token:
        return None
    credential = base64.b64encode(
        f"x-access-token:{token}".encode("utf-8")
    ).decode("ascii")
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
            "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {credential}",
        }
    )
    return environment


def _output_text(
    value: str | bytes | None,
    limit: int | None = MAX_CAPTURE_BYTES,
    strip: bool = True,
) -> str:
    if isinstance(value, bytes):
        data = value
    elif value:
        data = value.encode("utf-8")
    else:
        return ""
    truncated = limit is not None and len(data) > limit
    if truncated:
        omitted = len(data) - limit
        data = data[-limit:]
    text = data.decode("utf-8", errors="replace")
    if strip:
        text = text.strip()
    if truncated:
        return f"[... {omitted} bytes truncated ...]\n{text}"
    return text


def _captured_output(
    stream: object,
    limit: int | None,
    strip: bool = True,
) -> str:
    stream.flush()
    size = stream.tell()
    if limit is not None and size > limit:
        stream.seek(size - limit)
        data = stream.read()
        return (
            f"[... {size - limit} bytes truncated ...]\n"
            f"{_output_text(data, None, strip)}"
        )
    stream.seek(0)
    return _output_text(stream.read(), limit, strip)


def run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: int,
    label: str,
    check: bool = True,
    env: Mapping[str, str] | None = None,
    capture_limit: int | None = MAX_CAPTURE_BYTES,
    strip_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    with (
        tempfile.TemporaryFile() as stdout_file,
        tempfile.TemporaryFile() as stderr_file,
    ):
        try:
            completed = subprocess.run(
                args,
                cwd=cwd,
                check=False,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=timeout,
                env=env,
            )
        except subprocess.TimeoutExpired as error:
            stdout = _captured_output(
                stdout_file, capture_limit, strip_output
            ) or _output_text(
                error.stdout, capture_limit, strip_output
            )
            stderr = _captured_output(
                stderr_file, capture_limit, strip_output
            ) or _output_text(
                error.stderr, capture_limit, strip_output
            )
            diagnostics = []
            if stdout:
                diagnostics.append(f"stdout: {stdout}")
            if stderr:
                diagnostics.append(f"stderr: {stderr}")
            detail = f": {'; '.join(diagnostics)}" if diagnostics else ""
            raise CommandError(f"{label} timed out after {timeout}s{detail}") from error
        except subprocess.CalledProcessError as error:
            stdout = _captured_output(
                stdout_file, capture_limit, strip_output
            ) or _output_text(
                error.stdout, capture_limit, strip_output
            )
            stderr = _captured_output(
                stderr_file, capture_limit, strip_output
            ) or _output_text(
                error.stderr, capture_limit, strip_output
            )
            diagnostics = []
            if stdout:
                diagnostics.append(f"stdout: {stdout}")
            if stderr:
                diagnostics.append(f"stderr: {stderr}")
            detail = f": {'; '.join(diagnostics)}" if diagnostics else ""
            raise CommandError(
                f"{label} failed with exit code {error.returncode}{detail}"
            ) from error

        stdout = (
            _output_text(completed.stdout, capture_limit, strip_output)
            if completed.stdout is not None
            else _captured_output(stdout_file, capture_limit, strip_output)
        )
        stderr = (
            _output_text(completed.stderr, capture_limit, strip_output)
            if completed.stderr is not None
            else _captured_output(stderr_file, capture_limit, strip_output)
        )
        result = subprocess.CompletedProcess(args, completed.returncode, stdout, stderr)
        if check and result.returncode != 0:
            diagnostics = []
            if stdout:
                diagnostics.append(f"stdout: {stdout}")
            if stderr:
                diagnostics.append(f"stderr: {stderr}")
            detail = f": {'; '.join(diagnostics)}" if diagnostics else ""
            raise CommandError(
                f"{label} failed with exit code {result.returncode}{detail}"
            )
        return result


def run_git(
    *args: str,
    cwd: Path,
    timeout: int,
    strip: bool = True,
    env: Mapping[str, str] | None = None,
    capture_limit: int | None = MAX_CAPTURE_BYTES,
) -> str:
    result = run_command(
        ["git", *args],
        cwd=cwd,
        timeout=timeout,
        label=f"git {' '.join(args)}",
        env=env,
        capture_limit=capture_limit,
        strip_output=strip,
    )
    return result.stdout.strip() if strip else result.stdout
