from __future__ import annotations

import re
import unittest
from pathlib import Path

import validate_consumer


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {"think-challenge", "think-grill", "think-ramble"}


class SourceContractTests(unittest.TestCase):
    def test_manifest_is_dependency_free_source_package(self) -> None:
        manifest = (ROOT / "apm.yml").read_text(encoding="utf-8")

        self.assertIn("name: think\n", manifest)
        self.assertIn("version: 0.1.0\n", manifest)
        self.assertIn("license: Apache-2.0\n", manifest)
        self.assertIn(
            "repository: https://github.com/sergio-sisternes-epam/think\n",
            manifest,
        )
        self.assertNotRegex(manifest, r"(?m)^dependencies:")
        self.assertNotIn("#main", manifest)
        self.assertFalse((ROOT / "apm.lock.yaml").exists())

    def test_exact_skill_source_set_and_frontmatter(self) -> None:
        skill_files = sorted((ROOT / ".apm/skills").glob("*/SKILL.md"))
        names = set()
        for skill_file in skill_files:
            content = skill_file.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*(\S+)\s*$", content)
            self.assertIsNotNone(match, skill_file)
            names.add(match.group(1))
            self.assertTrue(content.startswith("---\n"), skill_file)
        self.assertEqual(names, EXPECTED_SKILLS)

    def test_generated_deployment_state_is_not_tracked(self) -> None:
        for relative in (".agents", ".claude", ".cursor", ".grok", "apm_modules"):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_release_workflow_uses_authoritative_remote_tag(self) -> None:
        release = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        helper = (ROOT / "scripts/release_tag.py").read_text(encoding="utf-8")

        self.assertIn("refs/release-tags/", helper)
        self.assertIn("--github-output \"$GITHUB_OUTPUT\"", release)
        self.assertNotIn("git cat-file -t \"$TAG_REF\"", release)
        self.assertIn("pull_request:", ci)
        self.assertIn('if [ "$REF_CREATED" != true ]', release)
        self.assertIn('EXPECTED_TAG_OBJECT:', release)
        self.assertIn(
            '[ "$REVERIFIED_TAG_OBJECT" != "$EXPECTED_TAG_OBJECT" ]',
            release,
        )
        self.assertIn(
            '[ "$REVERIFIED_CANDIDATE" != "$EXPECTED_CANDIDATE" ]',
            release,
        )
        for result in ("METADATA_RESULT", "SOURCE_RESULT", "CONSUMER_RESULT"):
            self.assertIn(f'[ "${result}" != success ]', ci)
        self.assertIn(
            '--require-current-main',
            ci,
        )
        self.assertNotIn("main_revision=\"$(git rev-parse", ci)
        self.assertIn(
            "candidate_revision: ${{ needs.candidate.outputs.candidate_revision }}",
            release,
        )
        self.assertIn(
            "package_source: sergio-sisternes-epam/think#${{ github.ref_name }}",
            release,
        )
        self.assertLess(
            ci.index("Validate reusable candidate revision"),
            ci.index("uses: actions/checkout@"),
        )
        self.assertNotIn("APM_READ_TOKEN", ci + release)
        self.assertNotIn("secrets: inherit", ci + release)
        self.assertIn("python3 scripts/audit_source.py", ci)
        self.assertIn("--jobs 8", ci)
        self.assertIn('--source "$PACKAGE_SOURCE"', ci)
        self.assertIn('--expected-revision "$EXPECTED_REVISION"', ci)
        self.assertIn("GITHUB_TOKEN: ${{ inputs.package_source != ''", ci)
        self.assertIn("workflow_dispatch:\n    inputs:\n      candidate_revision:", ci)
        self.assertIn(
            '[[ "$PACKAGE_SOURCE" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[A-Za-z0-9._/-]+$ ]]',
            ci,
        )
        self.assertIn("consumer:\n    name:", ci)
        self.assertIn("needs: metadata", ci)
        self.assertGreaterEqual((ci + release).count("persist-credentials: false"), 5)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", release)
        self.assertIn("python3 scripts/release_notes.py", release)
        self.assertIn('--notes "$release_notes"', release)

    def test_skills_only_package_does_not_use_compile_gate(self) -> None:
        workflows = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in (".github/workflows/ci.yml", ".github/workflows/release.yml")
        )
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertNotIn("apm compile", workflows)
        self.assertIn("`apm compile` is not a validation gate", contributing)

    def test_consumer_validation_is_repository_owned(self) -> None:
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn(
            '--target "$TARGETS"',
            ci,
        )

    def test_external_actions_are_commit_pinned(self) -> None:
        for relative in (".github/workflows/ci.yml", ".github/workflows/release.yml"):
            content = (ROOT / relative).read_text(encoding="utf-8")
            external_uses = re.findall(r"(?m)^\s*-\s+uses:\s+([^./][^@\s]*)@(\S+)", content)
            self.assertTrue(external_uses, relative)
            for action, revision in external_uses:
                self.assertRegex(revision, r"^[0-9a-f]{40}$", action)

    def test_apm_archive_is_checksum_pinned_before_execution(self) -> None:
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        setup = (ROOT / ".github/actions/setup-apm/action.yml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("microsoft/apm-action", ci)
        self.assertEqual(ci.count("uses: ./.github/actions/setup-apm"), 2)
        self.assertIn(
            'APM_LINUX_X64_SHA256: "53c98c50f436a8b5ac1d6a3cf443f94d29ed1e5385af52859cf1b1b512f71578"',
            ci,
        )
        self.assertLess(setup.index("sha256sum"), setup.index("tar -xzf"))
        self.assertLess(setup.index("tar -xzf"), setup.index('"$binary_dir/apm" --version'))
        self.assertNotIn("install -m", setup)

    def test_runtime_target_profiles_match_workflow_and_readme(self) -> None:
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for name, targets in validate_consumer.TARGET_PROFILES.items():
            target_list = ",".join(targets)
            self.assertIn(f"- name: {name}\n", ci)
            self.assertIn(f"target: {target_list}\n", ci)
            self.assertIn(f"--target {target_list}", readme)

    def test_apm_cli_version_surfaces_match(self) -> None:
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        issue_template = (
            ROOT / ".github/ISSUE_TEMPLATE/bug_report.md"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        versions = {
            re.search(r'(?m)^\s*APM_VERSION:\s*"([^"]+)"$', ci).group(1),
            re.search(r"(?m)^\| APM CLI \| ([^ ]+)", contributing).group(1),
            re.search(
                r"(?m)^- \*\*APM CLI version:\*\* e\.g\. ([^\s]+)",
                issue_template,
            ).group(1),
            re.search(r"Think is validated with APM CLI ([^ ]+)", readme).group(1),
        }
        self.assertEqual(versions, {"0.29.0"})


if __name__ == "__main__":
    unittest.main()
