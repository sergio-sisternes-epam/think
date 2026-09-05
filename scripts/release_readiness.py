#!/usr/bin/env python3
"""Validate Think release metadata against one package version."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from ci_output import emit_error, print_summary, write_github_outputs
from command_runner import run_git


ROOT = Path(__file__).resolve().parents[1]
GIT_TIMEOUT_SECONDS = 120
VERSION_NUMBER = r"(?:0|[1-9][0-9]*)"
CORE_VERSION = rf"{VERSION_NUMBER}\.{VERSION_NUMBER}\.{VERSION_NUMBER}"
NON_NUMERIC_IDENTIFIER = r"[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*"
PRERELEASE_IDENTIFIER = rf"(?:0|[1-9][0-9]*|{NON_NUMERIC_IDENTIFIER})"
SEMVER = (
    rf"(?:{CORE_VERSION})"
    rf"(?:-{PRERELEASE_IDENTIFIER}(?:\.{PRERELEASE_IDENTIFIER})*)?"
)


@dataclass(frozen=True)
class VersionSurface:
    label: str
    path: str
    pattern: str


SURFACES = (
    VersionSurface("manifest", "apm.yml", rf"^version:\s*({SEMVER})\s*$"),
    VersionSurface(
        "install command",
        "README.md",
        rf"^apm install sergio-sisternes-epam/think#v({SEMVER})"
        rf"\s+--target\s+agent-skills\s*$",
    ),
    VersionSurface(
        "stable-runtime install command",
        "README.md",
        rf"^apm install sergio-sisternes-epam/think#v({SEMVER})"
        rf"\s+--target\s+claude,codex,copilot,cursor,gemini,grok-build,"
        rf"kiro,opencode,windsurf\s*$",
    ),
    VersionSurface(
        "bug report example",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        rf"^- \*\*Package \(if applicable\):\*\* e\.g\. think-grill v({SEMVER})\s*$",
    ),
    VersionSurface(
        "changelog comparison base",
        "CHANGELOG.md",
        rf"^\[Unreleased\]: .+/compare/v({SEMVER})\.\.\.HEAD\s*$",
    ),
)
CHANGELOG_PATTERN = (
    rf"^## \[({SEMVER})\] - [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}\s*$"
)


def read_surface(
    surface: VersionSurface,
    root: Path = ROOT,
    contents: dict[str, str] | None = None,
) -> str:
    if contents is None:
        content = (root / surface.path).read_text(encoding="utf-8")
    else:
        if surface.path not in contents:
            contents[surface.path] = (root / surface.path).read_text(
                encoding="utf-8"
            )
        content = contents[surface.path]
    matches = re.findall(surface.pattern, content, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(
            f"{surface.path}: expected one {surface.label} version, "
            f"found {len(matches)}"
        )
    return matches[0]


def manifest_version(
    root: Path = ROOT,
    contents: dict[str, str] | None = None,
) -> str:
    return read_surface(SURFACES[0], root, contents)


def validate_versions(root: Path = ROOT) -> tuple[str | None, list[str]]:
    contents: dict[str, str] = {}
    try:
        expected = manifest_version(root, contents)
    except (OSError, ValueError) as error:
        return None, [str(error)]

    errors: list[str] = []
    for surface in SURFACES[1:]:
        try:
            actual = read_surface(surface, root, contents)
        except (OSError, ValueError) as error:
            errors.append(str(error))
            continue
        if actual != expected:
            errors.append(
                f"{surface.path}: {surface.label} version {actual} != {expected}"
            )

    release_link = VersionSurface(
        "changelog release link",
        "CHANGELOG.md",
        rf"^\[{re.escape(expected)}\]: .+/releases/tag/v({SEMVER})\s*$",
    )
    try:
        actual = read_surface(release_link, root, contents)
    except (OSError, ValueError) as error:
        errors.append(str(error))
    else:
        if actual != expected:
            errors.append(
                "CHANGELOG.md: changelog release link version "
                f"{actual} != {expected}"
            )

    try:
        changelog = contents["CHANGELOG.md"]
        changelog_versions = re.findall(CHANGELOG_PATTERN, changelog, re.MULTILINE)
    except OSError as error:
        errors.append(str(error))
    else:
        count = changelog_versions.count(expected)
        if count != 1:
            errors.append(
                "CHANGELOG.md: expected one current package version "
                f"{expected}, found {count}"
            )

    return expected, errors


def git(*args: str, root: Path = ROOT) -> str:
    return run_git(
        *args,
        cwd=root,
        timeout=GIT_TIMEOUT_SECONDS,
    )


def current_commit(root: Path = ROOT) -> str:
    return git("rev-parse", "HEAD", root=root)


def current_main_revision(root: Path = ROOT, remote: str = "origin") -> str:
    git(
        "fetch",
        "--no-tags",
        remote,
        "+refs/heads/main:refs/remotes/origin/main",
        root=root,
    )
    return git("rev-parse", "refs/remotes/origin/main", root=root)


def validate_commit(candidate: str, root: Path = ROOT) -> list[str]:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", candidate):
        return [f"candidate commit must be a 40-character SHA: {candidate}"]

    actual = current_commit(root)
    if candidate.lower() != actual.lower():
        return [f"candidate commit {candidate} != checked-out revision {actual}"]
    return []


def validate_current_main(
    candidate: str,
    root: Path = ROOT,
) -> tuple[str | None, list[str]]:
    try:
        main_revision = current_main_revision(root)
    except RuntimeError as error:
        return None, [str(error)]
    if candidate.lower() != main_revision.lower():
        return main_revision, [
            f"candidate commit {candidate} != exact current main {main_revision}"
        ]
    return main_revision, []


def is_prerelease(version: str) -> bool:
    return "-" in version


def validate_tag(tag: str, version: str) -> list[str]:
    expected = f"v{version}"
    return [] if tag == expected else [f"release tag {tag} != {expected}"]


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Pushed release tag to compare with apm.yml")
    parser.add_argument("--commit", help="Candidate commit SHA")
    parser.add_argument(
        "--require-current-main",
        action="store_true",
        help="Fetch origin/main and require the candidate to match it exactly",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file",
    )
    args = parser.parse_args(argv)
    if args.require_current_main and not args.commit:
        parser.error("--require-current-main requires --commit")

    version, version_errors = validate_versions(root)
    if version is None:
        print_summary(
            {
                "candidate_revision": "unknown",
                "package_version": "unknown",
                "expected_tag": "unknown",
                "is_prerelease": "unknown",
                "version_consistency": "blocked",
            }
        )
        for error in version_errors:
            emit_error(error)
        print("release_metadata_decision=blocked")
        write_github_outputs(
            args.github_output,
            {
                "candidate_revision": "unknown",
                "package_version": "unknown",
                "expected_tag": "unknown",
                "is_prerelease": "unknown",
                "version_consistency": "blocked",
                "release_metadata_decision": "blocked",
            },
        )
        return 1

    tag_errors = validate_tag(args.tag, version) if args.tag else []
    commit_errors = validate_commit(args.commit, root) if args.commit else []
    main_revision = None
    main_errors: list[str] = []
    if args.require_current_main and not commit_errors:
        main_revision, main_errors = validate_current_main(args.commit, root)
    errors = version_errors + tag_errors + commit_errors + main_errors
    candidate_revision = args.commit or current_commit(root)

    summary: dict[str, str] = {
        "candidate_revision": candidate_revision,
        "package_version": version,
        "expected_tag": f"v{version}",
        "is_prerelease": str(is_prerelease(version)).lower(),
        "version_consistency": "blocked" if version_errors else "pass",
    }
    if args.tag:
        summary["tag_consistency"] = "blocked" if tag_errors else "pass"
    if args.commit:
        summary["commit_consistency"] = "blocked" if commit_errors else "pass"
    if args.require_current_main:
        summary["main_revision"] = main_revision or "unknown"
        summary["current_main_consistency"] = "blocked" if main_errors else "pass"
    print_summary(summary)

    decision = "blocked" if errors else "pass"
    if errors:
        for error in errors:
            emit_error(error)
    print(f"release_metadata_decision={decision}")

    fields: dict[str, str] = {
        "candidate_revision": candidate_revision,
        "package_version": version,
        "expected_tag": f"v{version}",
        "is_prerelease": str(is_prerelease(version)).lower(),
        "version_consistency": "blocked" if version_errors else "pass",
        "release_metadata_decision": decision,
    }
    if args.tag:
        fields["tag_consistency"] = "blocked" if tag_errors else "pass"
    if args.commit:
        fields["commit_consistency"] = "blocked" if commit_errors else "pass"
    if args.require_current_main:
        fields["main_revision"] = main_revision or "unknown"
        fields["current_main_consistency"] = "blocked" if main_errors else "pass"
    write_github_outputs(args.github_output, fields)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
