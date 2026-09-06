from __future__ import annotations

import base64
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_tag


class ReleaseTagTests(unittest.TestCase):
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

    def git(self, root: Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def create_remote(self, root: Path) -> tuple[Path, Path, str]:
        remote = root / "remote.git"
        source = root / "source"
        self.git(root, "init", "--bare", str(remote))
        self.git(root, "init", "-b", "main", str(source))
        self.git(source, "config", "user.name", "Release Test")
        self.git(source, "config", "user.email", "release@example.com")
        (source / "package.txt").write_text("candidate\n", encoding="utf-8")
        self.git(source, "add", "package.txt")
        self.git(source, "commit", "-m", "Release candidate")
        commit = self.git(source, "rev-parse", "HEAD")
        self.git(source, "remote", "add", "origin", str(remote))
        self.git(source, "push", "origin", "main")
        return remote, source, commit

    def clone_checkout(self, root: Path, remote: Path, commit: str) -> Path:
        checkout = root / "checkout"
        self.git(root, "clone", "--no-tags", str(remote), str(checkout))
        self.git(checkout, "checkout", "--detach", commit)
        return checkout

    def test_remote_annotated_tag_survives_checkout_ref_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, source, commit = self.create_remote(root)
            self.git(source, "tag", "-a", "v0.1.0", "-m", "Think v0.1.0")
            self.git(source, "push", "origin", "refs/tags/v0.1.0")
            checkout = self.clone_checkout(root, remote, commit)

            self.git(
                checkout,
                "fetch",
                "--no-tags",
                "origin",
                f"{commit}:refs/tags/v0.1.0",
            )
            self.assertEqual(
                self.git(checkout, "cat-file", "-t", "refs/tags/v0.1.0"),
                "commit",
            )

            verified = release_tag.verify_remote_tag("v0.1.0", checkout)

            self.assertEqual(verified.tag_ref, "refs/release-tags/v0.1.0")
            self.assertEqual(verified.candidate_revision, commit)
            self.assertEqual(verified.main_revision, commit)
            self.assertEqual(
                self.git(checkout, "cat-file", "-t", verified.tag_ref), "tag"
            )
            self.assertEqual(
                self.git(checkout, "cat-file", "-t", "refs/tags/v0.1.0"),
                "commit",
            )

    def test_tag_validation_uses_selected_non_origin_remote_ref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, source, commit = self.create_remote(root)
            self.git(source, "tag", "-a", "v0.1.0", "-m", "Think v0.1.0")
            self.git(source, "push", "origin", "refs/tags/v0.1.0")
            checkout = self.clone_checkout(root, remote, commit)
            self.git(checkout, "remote", "rename", "origin", "upstream")
            self.git(
                checkout,
                "update-ref",
                "-d",
                "refs/remotes/upstream/main",
            )

            verified = release_tag.verify_remote_tag(
                "v0.1.0",
                checkout,
                remote="upstream",
            )

            self.assertEqual(verified.candidate_revision, commit)
            self.assertEqual(verified.main_revision, commit)
            self.assertEqual(
                self.git(checkout, "rev-parse", "refs/remotes/upstream/main"),
                commit,
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

    def test_lightweight_remote_tag_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, source, commit = self.create_remote(root)
            self.git(source, "tag", "v0.1.0")
            self.git(source, "push", "origin", "refs/tags/v0.1.0")
            checkout = self.clone_checkout(root, remote, commit)

            with self.assertRaisesRegex(
                release_tag.ReleaseTagError, "not an annotated tag object"
            ):
                release_tag.verify_remote_tag("v0.1.0", checkout)

    def test_remote_fetch_receives_ephemeral_git_auth_environment(self) -> None:
        with mock.patch.object(release_tag, "run_git", return_value="value") as run_git:
            release_tag.git("fetch", "origin", root=Path("."), token="secret")

        environment = run_git.call_args.kwargs["env"]
        self.assertEqual(environment["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(
            environment["GIT_CONFIG_KEY_0"],
            "http.https://github.com/.extraheader",
        )
        self.assertEqual(
            environment["GIT_CONFIG_VALUE_0"],
            "AUTHORIZATION: basic "
            + base64.b64encode(b"x-access-token:secret").decode("ascii"),
        )

    def test_tag_not_on_current_main_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, source, tagged_commit = self.create_remote(root)
            self.git(source, "tag", "-a", "v0.1.0", "-m", "Think v0.1.0")
            (source / "package.txt").write_text("advanced main\n", encoding="utf-8")
            self.git(source, "commit", "-am", "Advance main")
            main_commit = self.git(source, "rev-parse", "HEAD")
            self.git(source, "push", "origin", "main", "refs/tags/v0.1.0")
            checkout = self.clone_checkout(root, remote, tagged_commit)

            with self.assertRaisesRegex(
                release_tag.ReleaseTagError,
                f"peels to {tagged_commit}, not exact current main {main_commit}",
            ):
                release_tag.verify_remote_tag("v0.1.0", checkout)

    def test_cli_failure_emits_github_annotation(self) -> None:
        stderr = StringIO()

        with mock.patch.object(
            release_tag,
            "verify_remote_tag",
            side_effect=release_tag.ReleaseTagError("missing%tag"),
        ):
            with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
                with mock.patch.object(sys, "argv", ["release_tag.py", "--tag", "v0.1.0"]):
                    with redirect_stderr(stderr):
                        status = release_tag.main()

        self.assertEqual(status, 1)
        self.assertIn(
            "::error title=Release tag verification failed::"
            "release tag verification failed: missing%25tag",
            stderr.getvalue(),
        )

    def test_cli_success_writes_verified_github_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, source, commit = self.create_remote(root)
            self.git(source, "tag", "-a", "v0.1.0", "-m", "Think v0.1.0")
            self.git(source, "push", "origin", "refs/tags/v0.1.0")
            checkout = self.clone_checkout(root, remote, commit)
            output_path = root / "github-output"

            status = release_tag.main(
                [
                    "--tag",
                    "v0.1.0",
                    "--github-output",
                    str(output_path),
                ],
                checkout,
            )

            self.assertEqual(status, 0)
            outputs = self.read_outputs(output_path)
            self.assertEqual(outputs["tag_ref"], "refs/release-tags/v0.1.0")
            self.assertEqual(outputs["candidate_revision"], commit)
            self.assertEqual(outputs["main_revision"], commit)
            self.assertRegex(outputs["tag_object"], r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
