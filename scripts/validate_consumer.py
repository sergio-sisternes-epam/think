#!/usr/bin/env python3
"""Install Think into a disposable consumer and verify frozen replay."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from ci_output import emit_error, write_github_outputs


ROOT = Path(__file__).resolve().parents[1]
COMMAND_TIMEOUT_SECONDS = 300
EXPECTED_SKILLS = ("think-challenge", "think-grill", "think-ramble")
SHARED_TARGETS = {
    "agent-skills",
    "codex",
    "copilot",
    "cursor",
    "gemini",
    "opencode",
    "windsurf",
}
NATIVE_TARGETS = {"claude", "grok-build", "kiro"}
SUPPORTED_TARGETS = SHARED_TARGETS | NATIVE_TARGETS


def run(
    *args: str,
    cwd: Path,
    phase: str,
    timeout: int = COMMAND_TIMEOUT_SECONDS,
) -> None:
    print(f"consumer_phase={phase}:start")
    try:
        subprocess.run(
            args,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{phase} timed out after {timeout}s") from error
    except subprocess.CalledProcessError as error:
        diagnostic = error.stderr.strip() or error.stdout.strip()
        detail = f": {diagnostic}" if diagnostic else ""
        raise RuntimeError(
            f"{phase} failed with exit code {error.returncode}{detail}"
        ) from error
    print(f"consumer_phase={phase}:pass")


def digest(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"{path}: expected generated consumer lock is missing")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_targets(target: str) -> set[str]:
    targets = {value.strip() for value in target.split(",") if value.strip()}
    unsupported = targets - SUPPORTED_TARGETS
    if unsupported:
        raise RuntimeError(
            f"unsupported APM target(s): {', '.join(sorted(unsupported))}"
        )
    if not targets:
        raise RuntimeError("at least one supported APM target is required")
    return targets


def expected_skill_roots(consumer: Path, target: str) -> tuple[Path, ...]:
    targets = parse_targets(target)
    roots = set()
    if targets & SHARED_TARGETS:
        roots.add(consumer / ".agents" / "skills")
    if "claude" in targets:
        roots.add(consumer / ".claude" / "skills")
    if "grok-build" in targets:
        roots.add(consumer / ".grok" / "skills")
    if "kiro" in targets:
        roots.add(consumer / ".kiro" / "skills")
    return tuple(sorted(roots))


def validate_skill_root(skills_root: Path) -> None:
    if not skills_root.is_dir():
        raise RuntimeError(
            f"{skills_root}: expected deployed skills directory is missing"
        )

    installed = {
        path.parent.name for path in skills_root.glob("*/SKILL.md")
    }
    expected = set(EXPECTED_SKILLS)
    if installed != expected:
        raise RuntimeError(
            f"installed skills mismatch: expected {sorted(expected)}, "
            f"actual {sorted(installed)}"
        )

    for skill in EXPECTED_SKILLS:
        skill_file = skills_root / skill / "SKILL.md"
        expected_name = f"name: {skill}"
        if expected_name not in skill_file.read_text(encoding="utf-8").splitlines():
            raise RuntimeError(f"{skill_file}: missing exact '{expected_name}'")


def validate_deployment(consumer: Path, target: str) -> None:
    roots = expected_skill_roots(consumer, target)
    if not roots:
        raise RuntimeError(f"no supported skill deployment root for target: {target}")
    for skills_root in roots:
        validate_skill_root(skills_root)


def validate_consumer_in_directory(
    source: Path,
    target: str,
    consumer: Path,
    runner: Callable[..., None] = run,
) -> str:
    parse_targets(target)
    runner("git", "init", "--quiet", cwd=consumer, phase="git-init")
    runner(
        "apm",
        "install",
        str(source),
        "--target",
        target,
        "--no-policy",
        cwd=consumer,
        phase="initial-install",
    )
    validate_deployment(consumer, target)

    lock = consumer / "apm.lock.yaml"
    before = digest(lock)
    runner(
        "apm",
        "install",
        "--frozen",
        "--target",
        target,
        "--no-policy",
        cwd=consumer,
        phase="frozen-replay",
    )
    after = digest(lock)
    if before != after:
        raise RuntimeError(
            f"frozen replay changed apm.lock.yaml: {before} != {after}"
        )

    runner(
        "apm",
        "audit",
        "--ci",
        "--no-policy",
        "--no-fail-fast",
        cwd=consumer,
        phase="consumer-audit",
    )
    return after


def validate_consumer(source: Path, target: str) -> str:
    with tempfile.TemporaryDirectory(prefix="think-consumer-") as directory:
        return validate_consumer_in_directory(source, target, Path(directory))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT,
        help="Checked-out Think package root",
    )
    parser.add_argument("--target", required=True, help="APM target list")
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file",
    )
    args = parser.parse_args(argv)

    try:
        lock_hash = validate_consumer(args.source.resolve(), args.target)
    except RuntimeError as error:
        emit_error(
            str(error),
            title="Consumer validation failed",
            file="scripts/validate_consumer.py",
        )
        fields = {
            "consumer_target": args.target,
            "consumer_validation": "failed",
        }
        write_github_outputs(args.github_output, fields)
        print("consumer_validation=failed")
        return 1

    fields = {
        "consumer_target": args.target,
        "installed_skills": ",".join(EXPECTED_SKILLS),
        "frozen_lock_sha256": lock_hash,
        "consumer_validation": "pass",
    }
    for key, value in fields.items():
        print(f"{key}={value}")
    write_github_outputs(args.github_output, fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
