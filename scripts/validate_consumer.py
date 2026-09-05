#!/usr/bin/env python3
"""Install Think into a disposable consumer and verify frozen replay."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = ("think-challenge", "think-grill", "think-ramble")


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def digest(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"{path}: expected generated consumer lock is missing")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_deployment(consumer: Path) -> None:
    skills_root = consumer / ".agents" / "skills"
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


def validate_consumer(source: Path, target: str) -> str:
    with tempfile.TemporaryDirectory(prefix="think-consumer-") as directory:
        consumer = Path(directory)
        run("git", "init", "--quiet", cwd=consumer)
        run(
            "apm",
            "install",
            str(source),
            "--target",
            target,
            "--no-policy",
            cwd=consumer,
        )
        validate_deployment(consumer)

        lock = consumer / "apm.lock.yaml"
        before = digest(lock)
        run(
            "apm",
            "install",
            "--frozen",
            "--target",
            target,
            "--no-policy",
            cwd=consumer,
        )
        after = digest(lock)
        if before != after:
            raise RuntimeError(
                f"frozen replay changed apm.lock.yaml: {before} != {after}"
            )

        run(
            "apm",
            "audit",
            "--ci",
            "--no-policy",
            "--no-fail-fast",
            cwd=consumer,
        )
        return after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT,
        help="Checked-out Think package root",
    )
    parser.add_argument("--target", required=True, help="APM target list")
    args = parser.parse_args()

    lock_hash = validate_consumer(args.source.resolve(), args.target)
    print(f"consumer_target={args.target}")
    print(f"installed_skills={','.join(EXPECTED_SKILLS)}")
    print(f"frozen_lock_sha256={lock_hash}")
    print("consumer_validation=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
