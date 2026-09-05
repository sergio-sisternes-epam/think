from __future__ import annotations

import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock
from pathlib import Path

import release_readiness


ROOT = Path(__file__).resolve().parents[1]


class ReleaseReadinessTests(unittest.TestCase):
    def read_outputs(self, path: Path) -> dict[str, str]:
        content = path.read_text(encoding="utf-8").splitlines()
        values = {}
        index = 0
        while index < len(content):
            key, delimiter = content[index].split("<<", 1)
            values[key] = content[index + 1]
            self.assertEqual(content[index + 2], delimiter)
            index += 3
        return values

    def test_repository_version_surfaces_match(self) -> None:
        version, errors = release_readiness.validate_versions(ROOT)

        self.assertEqual(version, "0.1.0")
        self.assertEqual(errors, [])
        self.assertFalse(release_readiness.is_prerelease(version))

    def test_mismatched_install_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "apm.yml",
                "README.md",
                "CHANGELOG.md",
                ".github/ISSUE_TEMPLATE/bug_report.md",
            ):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)

            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace(
                    "think#v0.1.0", "think#v0.2.0"
                ),
                encoding="utf-8",
            )

            version, errors = release_readiness.validate_versions(root)

            self.assertEqual(version, "0.1.0")
            self.assertTrue(
                any("install command version 0.2.0 != 0.1.0" in error for error in errors)
            )

    def test_invalid_semver_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "apm.yml").write_text(
                "name: think\nversion: 01.0.0\n", encoding="utf-8"
            )

            version, errors = release_readiness.validate_versions(root)

            self.assertIsNone(version)
            self.assertTrue(errors)

    def test_candidate_commit_validation_rejects_invalid_values(self) -> None:
        self.assertRegex(
            release_readiness.validate_commit("not-a-sha", ROOT)[0],
            "40-character SHA",
        )
        self.assertRegex(
            release_readiness.validate_commit("0" * 40, ROOT)[0],
            "!= checked-out revision",
        )

    def test_tag_validation_and_prerelease_classification(self) -> None:
        self.assertEqual(
            release_readiness.validate_tag("v0.1.0", "0.1.0"),
            [],
        )
        self.assertEqual(
            release_readiness.validate_tag("v0.2.0", "0.1.0"),
            ["release tag v0.2.0 != v0.1.0"],
        )
        self.assertTrue(release_readiness.is_prerelease("0.2.0-rc.1"))

    def test_errors_are_annotated_in_github_actions(self) -> None:
        output = StringIO()

        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
            with redirect_stdout(output):
                release_readiness.emit_error("bad%value\nnext")

        self.assertEqual(
            output.getvalue().splitlines(),
            ["error: bad%value", "next", "::error::bad%25value%0Anext"],
        )

    def test_cli_writes_stable_github_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output"
            commit = release_readiness.current_commit(ROOT)

            status = release_readiness.main(
                [
                    "--commit",
                    commit,
                    "--github-output",
                    str(output_path),
                ],
                ROOT,
            )

            self.assertEqual(status, 0)
            self.assertEqual(
                self.read_outputs(output_path),
                {
                    "candidate_revision": commit,
                    "package_version": "0.1.0",
                    "expected_tag": "v0.1.0",
                    "is_prerelease": "false",
                    "version_consistency": "pass",
                    "release_metadata_decision": "pass",
                    "commit_consistency": "pass",
                },
            )

    def test_exact_current_main_mismatch_is_rejected(self) -> None:
        with mock.patch.object(
            release_readiness,
            "current_main_revision",
            return_value="1" * 40,
        ):
            main_revision, errors = release_readiness.validate_current_main(
                "2" * 40,
                ROOT,
            )

        self.assertEqual(main_revision, "1" * 40)
        self.assertEqual(
            errors,
            [
                f"candidate commit {'2' * 40} != exact current main {'1' * 40}"
            ],
        )


if __name__ == "__main__":
    unittest.main()
