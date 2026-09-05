from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import command_runner


class CommandRunnerTests(unittest.TestCase):
    def test_success_returns_captured_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = command_runner.run_command(
                ["git", "--version"],
                cwd=Path(directory),
                timeout=30,
                label="git version",
            )

        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("git version "))

    def test_failure_includes_stderr_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                command_runner.CommandError,
                "git failure failed with exit code",
            ):
                command_runner.run_command(
                    ["git", "rev-parse", "--verify", "missing"],
                    cwd=Path(directory),
                    timeout=30,
                    label="git failure",
                )

    def test_timeout_has_bounded_diagnostic(self) -> None:
        with mock.patch(
            "command_runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["command"], 7),
        ):
            with self.assertRaisesRegex(
                command_runner.CommandError,
                "slow command timed out after 7s",
            ):
                command_runner.run_command(
                    ["command"],
                    cwd=Path("."),
                    timeout=7,
                    label="slow command",
                )

    def test_run_git_returns_stripped_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            version = command_runner.run_git(
                "--version",
                cwd=Path(directory),
                timeout=30,
            )

        self.assertRegex(version, r"^git version \S+$")


if __name__ == "__main__":
    unittest.main()
