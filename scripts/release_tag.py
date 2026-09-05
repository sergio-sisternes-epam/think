#!/usr/bin/env python3
"""Verify an authoritative remote release tag without trusting checkout tag refs."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from ci_output import emit_error, print_summary, write_github_outputs
from command_runner import CommandError, github_git_auth_environment, run_git


ROOT = Path(__file__).resolve().parents[1]
GIT_TIMEOUT_SECONDS = 120


class ReleaseTagError(RuntimeError):
    """Raised when a remote release tag is not a valid exact-main candidate."""


@dataclass(frozen=True)
class ReleaseTag:
    tag_ref: str
    tag_object: str
    candidate_revision: str
    main_revision: str


def git(
    *args: str,
    root: Path = ROOT,
    token: str | None = None,
) -> str:
    try:
        return run_git(
            *args,
            cwd=root,
            timeout=GIT_TIMEOUT_SECONDS,
            env=github_git_auth_environment(token),
        )
    except CommandError as error:
        raise ReleaseTagError(str(error)) from error


def verify_remote_tag(
    tag: str,
    root: Path = ROOT,
    remote: str = "origin",
    token: str | None = None,
) -> ReleaseTag:
    remote_ref = f"refs/tags/{tag}"
    tag_ref = f"refs/release-tags/{tag}"
    git("check-ref-format", remote_ref, root=root)
    git("check-ref-format", tag_ref, root=root)

    git(
        "fetch",
        "--no-tags",
        remote,
        f"{remote_ref}:{tag_ref}",
        "+refs/heads/main:refs/remotes/origin/main",
        root=root,
        token=token,
    )
    object_type = git("cat-file", "-t", tag_ref, root=root)
    if object_type != "tag":
        raise ReleaseTagError(
            f"{remote_ref} is {object_type}, not an annotated tag object"
        )

    tag_object = git("rev-parse", tag_ref, root=root)
    candidate_revision = git("rev-parse", f"{tag_ref}^{{commit}}", root=root)
    main_revision = git("rev-parse", "refs/remotes/origin/main", root=root)
    if candidate_revision != main_revision:
        raise ReleaseTagError(
            f"{remote_ref} peels to {candidate_revision}, "
            f"not exact current main {main_revision}"
        )

    return ReleaseTag(tag_ref, tag_object, candidate_revision, main_revision)


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag name")
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file",
    )
    args = parser.parse_args(argv)

    try:
        verified = verify_remote_tag(args.tag, root, token=os.environ.get("GITHUB_TOKEN"))
    except ReleaseTagError as error:
        emit_error(
            f"release tag verification failed: {error}",
            title="Release tag verification failed",
            stream=sys.stderr,
        )
        return 1

    fields = (
        ("tag_ref", verified.tag_ref),
        ("tag_object", verified.tag_object),
        ("candidate_revision", verified.candidate_revision),
        ("main_revision", verified.main_revision),
    )
    print_summary(dict(fields))
    write_github_outputs(args.github_output, dict(fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
