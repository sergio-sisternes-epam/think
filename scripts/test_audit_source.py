from __future__ import annotations

import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import audit_source
from command_runner import CommandError


class AuditSourceTests(unittest.TestCase):
    def git(self, root: Path, *args: str) -> None:
        __import__("subprocess").run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=30,
        )

    def test_tracked_files_excludes_untracked_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.git(root, "init", "--quiet")
            (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            (root / "untracked.txt").write_text("untracked\n", encoding="utf-8")
            self.git(root, "add", "tracked.txt")

            self.assertEqual(audit_source.tracked_files(root), ["tracked.txt"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_tracked_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.git(root, "init", "--quiet")
            (root / "target.txt").write_text("target\n", encoding="utf-8")
            (root / "link.txt").symlink_to("target.txt")
            self.git(root, "add", "link.txt")

            with self.assertRaisesRegex(
                audit_source.SourceAuditError,
                "tracked symbolic links are not auditable",
            ):
                audit_source.tracked_files(root)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_tracked_path_escaping_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "file.txt").write_text("outside\n", encoding="utf-8")
            (root / "linked").symlink_to(outside, target_is_directory=True)

            with mock.patch(
                "audit_source.run_git",
                return_value="linked/file.txt\0",
            ):
                with self.assertRaisesRegex(
                    audit_source.SourceAuditError,
                    "tracked path escapes the repository",
                ):
                    audit_source.tracked_files(root)

    def test_timeout_becomes_actionable_audit_failure(self) -> None:
        with mock.patch(
            "audit_source.run_command",
            side_effect=CommandError("APM source audit for apm.yml timed out after 5s"),
        ):
            result = audit_source.audit_file("apm.yml", timeout=5)

        self.assertEqual(result.returncode, 124)
        self.assertIn("timed out after 5s", result.output)

    def test_mixed_results_emit_diagnostic_annotation_and_fail(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        results = [
            audit_source.AuditResult("apm.yml", 0, "ok"),
            audit_source.AuditResult("README.md", 1, "invalid frontmatter\nmore"),
        ]

        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
            with redirect_stdout(stdout):
                with mock.patch("sys.stderr", stderr):
                    status = audit_source.report_results(results)

        self.assertEqual(status, 1)
        self.assertIn(
            "::error title=APM source audit failed,file=README.md::"
            "APM source audit failed: invalid frontmatter",
            stderr.getvalue(),
        )
        self.assertIn("source_audit_failures=1", stdout.getvalue())

    def test_report_writes_github_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output"

            status = audit_source.report_results(
                [audit_source.AuditResult("apm.yml", 0, "ok")],
                output_path,
            )

            self.assertEqual(status, 0)
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("source_audit_files<<", content)
            self.assertIn("\n1\n", content)
            self.assertIn("source_audit<<", content)
            self.assertIn("\npass\n", content)


if __name__ == "__main__":
    unittest.main()
