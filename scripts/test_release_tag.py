from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_tag


class ReleaseTagTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
