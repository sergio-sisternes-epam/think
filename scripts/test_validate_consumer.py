from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import validate_consumer


class ValidateConsumerTests(unittest.TestCase):
    def deploy_skills(self, consumer: Path, target: str) -> None:
        for root in validate_consumer.expected_skill_roots(consumer, target):
            for skill in validate_consumer.EXPECTED_SKILLS:
                skill_file = root / skill / "SKILL.md"
                skill_file.parent.mkdir(parents=True, exist_ok=True)
                skill_file.write_text(
                    f"---\nname: {skill}\n---\n",
                    encoding="utf-8",
                )

    def test_missing_skills_directory_has_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)

            with self.assertRaisesRegex(
                RuntimeError,
                "expected deployed skills directory is missing",
            ):
                validate_consumer.validate_deployment(consumer, "agent-skills")

    def test_skill_mismatch_reports_expected_and_actual(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            skill_root = consumer / ".agents" / "skills" / "think-grill"
            skill_root.mkdir(parents=True)
            (skill_root / "SKILL.md").write_text(
                "---\nname: think-grill\n---\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                RuntimeError,
                r"expected \['think-challenge', 'think-grill', 'think-ramble'\], "
                r"actual \['think-grill'\]",
            ):
                validate_consumer.validate_deployment(consumer, "agent-skills")

    def test_missing_lock_has_actionable_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / "apm.lock.yaml"

            with self.assertRaisesRegex(
                RuntimeError,
                "expected generated consumer lock is missing",
            ):
                validate_consumer.digest(lock)

    def test_stable_targets_require_all_native_skill_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            target = (
                "claude,codex,copilot,cursor,gemini,grok-build,"
                "kiro,opencode,windsurf"
            )

            roots = validate_consumer.expected_skill_roots(consumer, target)

            self.assertEqual(
                {root.relative_to(consumer).as_posix() for root in roots},
                {
                    ".agents/skills",
                    ".claude/skills",
                    ".grok/skills",
                    ".kiro/skills",
                },
            )

    def test_each_native_target_uses_its_documented_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            expected = {
                "claude": ".claude/skills",
                "grok-build": ".grok/skills",
                "kiro": ".kiro/skills",
            }

            for target, relative in expected.items():
                with self.subTest(target=target):
                    roots = validate_consumer.expected_skill_roots(consumer, target)
                    self.assertEqual(
                        [root.relative_to(consumer).as_posix() for root in roots],
                        [relative],
                    )

    def test_unsupported_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                RuntimeError,
                "unsupported APM target\\(s\\): unknown",
            ):
                validate_consumer.expected_skill_roots(
                    Path(directory),
                    "agent-skills,unknown",
                )

    def test_frozen_lock_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            target = "agent-skills"

            def fake_runner(
                *args: str,
                cwd: Path,
                phase: str,
                timeout: int = validate_consumer.COMMAND_TIMEOUT_SECONDS,
            ) -> None:
                del args, timeout
                if phase == "initial-install":
                    self.deploy_skills(cwd, target)
                    (cwd / "apm.lock.yaml").write_text("before\n", encoding="utf-8")
                elif phase == "frozen-replay":
                    (cwd / "apm.lock.yaml").write_text("after\n", encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "frozen replay changed apm.lock.yaml",
            ):
                validate_consumer.validate_consumer_in_directory(
                    Path("/source"),
                    target,
                    consumer,
                    runner=fake_runner,
                )

    def test_cli_failure_emits_annotation_and_status(self) -> None:
        output = StringIO()
        with mock.patch.object(
            validate_consumer,
            "validate_consumer",
            side_effect=RuntimeError("frozen replay failed"),
        ):
            with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
                with redirect_stdout(output):
                    status = validate_consumer.main(["--target", "agent-skills"])

        self.assertEqual(status, 1)
        self.assertIn(
            "::error title=Consumer validation failed,"
            "file=scripts/validate_consumer.py::frozen replay failed",
            output.getvalue(),
        )
        self.assertIn("consumer_validation=failed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
