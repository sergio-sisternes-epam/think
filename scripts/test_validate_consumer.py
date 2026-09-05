from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import validate_consumer


class ValidateConsumerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
