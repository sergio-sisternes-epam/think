from __future__ import annotations

import re
import unittest
from pathlib import Path


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
        self.assertIn('[ "$tag_object" != "$EXPECTED_TAG_OBJECT" ]', release)
        self.assertIn('[ "$tag_commit" != "$EXPECTED_CANDIDATE" ]', release)
        for result in ("METADATA_RESULT", "SOURCE_RESULT", "CONSUMER_RESULT"):
            self.assertIn(f'[ "${result}" != success ]', ci)
        self.assertIn(
            '[ "$CANDIDATE_REVISION" != "$main_revision" ]',
            ci,
        )
        self.assertIn(
            "candidate_revision: ${{ needs.candidate.outputs.candidate_revision }}",
            release,
        )
        self.assertLess(
            ci.index("Validate reusable candidate revision"),
            ci.index("uses: actions/checkout@"),
        )
        self.assertNotIn("APM_READ_TOKEN", ci + release)
        self.assertNotIn("secrets: inherit", ci + release)

    def test_consumer_validation_is_repository_owned(self) -> None:
        ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn(
            'python3 scripts/validate_consumer.py --target "$TARGETS"',
            ci,
        )

    def test_external_actions_are_commit_pinned(self) -> None:
        for relative in (".github/workflows/ci.yml", ".github/workflows/release.yml"):
            content = (ROOT / relative).read_text(encoding="utf-8")
            external_uses = re.findall(r"(?m)^\s*-\s+uses:\s+([^./][^@\s]*)@(\S+)", content)
            self.assertTrue(external_uses, relative)
            for action, revision in external_uses:
                self.assertRegex(revision, r"^[0-9a-f]{40}$", action)


if __name__ == "__main__":
    unittest.main()
