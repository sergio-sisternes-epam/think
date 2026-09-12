from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import mock
from pathlib import Path

import release_readiness


ROOT = Path(__file__).resolve().parents[1]


class ReleaseReadinessTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()

    def create_release_checkout(
        self,
        root: Path,
    ) -> tuple[Path, Path, str]:
        remote = root / "remote.git"
        source = root / "source"
        checkout = root / "checkout"
        self.git(root, "init", "--bare", str(remote))
        self.git(root, "init", "-b", "main", str(source))
        self.git(source, "config", "user.name", "Readiness Test")
        self.git(source, "config", "user.email", "readiness@example.com")
        for relative in (
            "apm.yml",
            "README.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            ".github/ISSUE_TEMPLATE/bug_report.md",
        ):
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        self.git(source, "add", ".")
        self.git(source, "commit", "-m", "Release candidate")
        commit = self.git(source, "rev-parse", "HEAD")
        self.git(source, "remote", "add", "origin", str(remote))
        self.git(source, "push", "origin", "main")
        self.git(root, "clone", "--no-tags", str(remote), str(checkout))
        self.git(checkout, "checkout", "--detach", commit)
        return source, checkout, commit

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
                "CONTRIBUTING.md",
                "CHANGELOG.md",
                ".github/ISSUE_TEMPLATE/bug_report.md",
            ):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)

            contributing = root / "CONTRIBUTING.md"
            contributing.write_text(
                contributing.read_text(encoding="utf-8").replace(
                    "think#v0.1.0", "think#v0.2.0"
                ),
                encoding="utf-8",
            )

            version, errors = release_readiness.validate_versions(root)

            self.assertEqual(version, "0.1.0")
            self.assertTrue(
                any("install command version 0.2.0 != 0.1.0" in error for error in errors)
            )

    def test_missing_changelog_returns_structured_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "apm.yml",
                "README.md",
                "CONTRIBUTING.md",
                ".github/ISSUE_TEMPLATE/bug_report.md",
            ):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)

            version, errors = release_readiness.validate_versions(root)

            self.assertEqual(version, "0.1.0")
            self.assertTrue(errors)
            self.assertTrue(all("CHANGELOG.md" in error for error in errors))

    def test_historical_release_links_do_not_break_current_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "apm.yml",
                "README.md",
                "CONTRIBUTING.md",
                "CHANGELOG.md",
                ".github/ISSUE_TEMPLATE/bug_report.md",
            ):
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            changelog = root / "CHANGELOG.md"
            changelog.write_text(
                changelog.read_text(encoding="utf-8")
                + "\n[0.0.9]: https://github.com/example/think/releases/tag/v0.0.9\n",
                encoding="utf-8",
            )

            version, errors = release_readiness.validate_versions(root)

            self.assertEqual(version, "0.1.0")
            self.assertEqual(errors, [])

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
            with redirect_stderr(output):
                release_readiness.emit_error("bad%value\nnext")

        self.assertEqual(
            output.getvalue().splitlines(),
            ["error: bad%value", "next", "::error::bad%25value next"],
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

    def test_cli_writes_tag_and_commit_consistency_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output"
            commit = release_readiness.current_commit(ROOT)

            status = release_readiness.main(
                [
                    "--tag",
                    "v0.1.0",
                    "--commit",
                    commit,
                    "--github-output",
                    str(output_path),
                ],
                ROOT,
            )

            outputs = self.read_outputs(output_path)
            self.assertEqual(status, 0)
            self.assertEqual(outputs["tag_consistency"], "pass")
            self.assertEqual(outputs["commit_consistency"], "pass")

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

    def test_current_main_fetch_receives_ephemeral_auth(self) -> None:
        with mock.patch.object(
            release_readiness,
            "run_git",
            side_effect=["", "", "a" * 40],
        ) as run_git:
            revision = release_readiness.current_main_revision(
                ROOT,
                token="secret",
            )

        self.assertEqual(revision, "a" * 40)
        self.assertIn("AUTHORIZATION: basic", run_git.call_args_list[1].kwargs["env"][
            "GIT_CONFIG_VALUE_0"
        ])

    def test_current_main_uses_selected_non_origin_remote_ref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, checkout, _ = self.create_release_checkout(root)
            self.git(checkout, "remote", "rename", "origin", "upstream")
            self.git(
                checkout,
                "update-ref",
                "-d",
                "refs/remotes/upstream/main",
            )

            (source / "advance.txt").write_text("advance\n", encoding="utf-8")
            self.git(source, "add", "advance.txt")
            self.git(source, "commit", "-m", "Advance main")
            self.git(source, "push", "origin", "main")
            expected = self.git(source, "rev-parse", "HEAD")

            revision = release_readiness.current_main_revision(
                checkout,
                remote="upstream",
            )

            self.assertEqual(revision, expected)
            self.assertEqual(
                self.git(checkout, "rev-parse", "refs/remotes/upstream/main"),
                expected,
            )
            result = subprocess.run(
                [
                    "git",
                    "show-ref",
                    "--verify",
                    "--quiet",
                    "refs/remotes/origin/main",
                ],
                cwd=checkout,
                check=False,
            )
            self.assertEqual(result.returncode, 1)

    def test_require_current_main_uses_real_detached_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, checkout, commit = self.create_release_checkout(root)

            status = release_readiness.main(
                ["--commit", commit, "--require-current-main"],
                checkout,
            )
            self.assertEqual(status, 0)

            (source / "advance.txt").write_text("advance\n", encoding="utf-8")
            self.git(source, "add", "advance.txt")
            self.git(source, "commit", "-m", "Advance main")
            self.git(source, "push", "origin", "main")

            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = release_readiness.main(
                    ["--commit", commit, "--require-current-main"],
                    checkout,
                )
            self.assertEqual(status, 1)
            self.assertIn("current_main_consistency=blocked", stdout.getvalue())
            self.assertIn("!= exact current main", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
