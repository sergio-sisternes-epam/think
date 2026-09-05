#!/usr/bin/env python3
"""Verify an authoritative remote release tag without trusting checkout tag refs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTagError(RuntimeError):
    """Raised when a remote release tag is not a valid exact-main candidate."""


@dataclass(frozen=True)
class ReleaseTag:
    tag_ref: str
    tag_object: str
    candidate_revision: str
    main_revision: str


def git(*args: str, root: Path = ROOT) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        diagnostic = error.stderr.strip() or error.stdout.strip()
        raise ReleaseTagError(diagnostic or f"git {' '.join(args)} failed") from error
    return result.stdout.strip()


def verify_remote_tag(
    tag: str, root: Path = ROOT, remote: str = "origin"
) -> ReleaseTag:
    remote_ref = f"refs/tags/{tag}"
    tag_ref = f"refs/release-tags/{tag}"
    git("check-ref-format", remote_ref, root=root)
    git("check-ref-format", tag_ref, root=root)

    git("fetch", "--no-tags", remote, f"{remote_ref}:{tag_ref}", root=root)
    object_type = git("cat-file", "-t", tag_ref, root=root)
    if object_type != "tag":
        raise ReleaseTagError(
            f"{remote_ref} is {object_type}, not an annotated tag object"
        )

    tag_object = git("rev-parse", tag_ref, root=root)
    candidate_revision = git("rev-parse", f"{tag_ref}^{{commit}}", root=root)
    git(
        "fetch",
        "--no-tags",
        remote,
        "+refs/heads/main:refs/remotes/origin/main",
        root=root,
    )
    main_revision = git("rev-parse", "refs/remotes/origin/main", root=root)
    if candidate_revision != main_revision:
        raise ReleaseTagError(
            f"{remote_ref} peels to {candidate_revision}, "
            f"not exact current main {main_revision}"
        )

    return ReleaseTag(tag_ref, tag_object, candidate_revision, main_revision)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag name")
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file",
    )
    args = parser.parse_args()

    try:
        verified = verify_remote_tag(args.tag)
    except ReleaseTagError as error:
        print(f"release tag verification failed: {error}", file=sys.stderr)
        return 1

    fields = (
        ("tag_ref", verified.tag_ref),
        ("tag_object", verified.tag_object),
        ("candidate_revision", verified.candidate_revision),
        ("main_revision", verified.main_revision),
    )
    for key, value in fields:
        print(f"{key}={value}")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as output:
            for key, value in fields:
                output.write(f"{key}={value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
