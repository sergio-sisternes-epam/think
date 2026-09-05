from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import validate_consumer


class ValidateConsumerTests(unittest.TestCase):
    def deploy_skills(self, consumer: Path, target: str) -> None:
        contract = validate_consumer.package_contract()
        for root in validate_consumer.expected_skill_roots(consumer, target):
            for skill in contract.skills:
                skill_file = root / skill / "SKILL.md"
                skill_file.parent.mkdir(parents=True, exist_ok=True)
                skill_file.write_text(
                    f"---\nname: {skill}\n---\n",
                    encoding="utf-8",
                )

    def write_valid_lock(
        self,
        consumer: Path,
        target: str,
        source: str | None = None,
    ) -> None:
        source = source or str(consumer)
        contract = validate_consumer.package_contract()
        hashes = []
        for root in validate_consumer.expected_skill_roots(consumer, target):
            for skill in contract.skills:
                skill_file = root / skill / "SKILL.md"
                relative = skill_file.relative_to(consumer).as_posix()
                hashes.append(
                    f"    {relative}: sha256:{validate_consumer.digest(skill_file)}"
                )
        provenance = []
        if "#" in source:
            repo, reference = source.rsplit("#", 1)
            provenance = [
                f"  repo_url: {repo}",
                f"  resolved_ref: {reference}",
                f"  resolved_commit: {'a' * 40}",
            ]
        else:
            provenance = [
                "  source: local",
                f"  local_path: {Path(source).resolve()}",
            ]
        (consumer / "apm.lock.yaml").write_text(
            "\n".join(
                [
                    "dependencies:",
                    f"- name: {contract.name}",
                    f"  version: {contract.version}",
                    "  deployed_file_hashes:",
                    *hashes,
                    *provenance,
                    "",
                ]
            ),
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

    def test_lock_requires_complete_matching_deployed_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            target = "agent-skills"
            self.deploy_skills(consumer, target)
            self.write_valid_lock(consumer, target, str(consumer))

            validate_consumer.validate_lock(
                consumer / "apm.lock.yaml",
                consumer,
                target,
                str(consumer),
            )

            lock = consumer / "apm.lock.yaml"
            first_skill = (
                consumer
                / ".agents"
                / "skills"
                / validate_consumer.package_contract().skills[0]
                / "SKILL.md"
            )
            actual_hash = validate_consumer.digest(first_skill)
            lock.write_text(
                lock.read_text(encoding="utf-8").replace(actual_hash, "0" * 64, 1),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "deployed hash mismatch"):
                validate_consumer.validate_lock(
                    lock,
                    consumer,
                    target,
                    str(consumer),
                )

    def test_remote_lock_requires_repo_ref_and_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            target = "agent-skills"
            source = "sergio-sisternes-epam/think#v0.1.0"
            self.deploy_skills(consumer, target)
            self.write_valid_lock(consumer, target, source)

            validate_consumer.validate_lock(
                consumer / "apm.lock.yaml",
                consumer,
                target,
                source,
                "a" * 40,
            )

            lock = consumer / "apm.lock.yaml"
            lock.write_text(
                lock.read_text(encoding="utf-8").replace(
                    "  resolved_ref: v0.1.0\n",
                    "",
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "missing source provenance"):
                validate_consumer.validate_lock(
                    lock,
                    consumer,
                    target,
                    source,
                    "a" * 40,
                )

    def test_remote_lock_must_match_expected_revision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            consumer = Path(directory)
            target = "agent-skills"
            source = "sergio-sisternes-epam/think#v0.1.0"
            self.deploy_skills(consumer, target)
            self.write_valid_lock(consumer, target, source)

            with self.assertRaisesRegex(RuntimeError, "!= expected"):
                validate_consumer.validate_lock(
                    consumer / "apm.lock.yaml",
                    consumer,
                    target,
                    source,
                    "b" * 40,
                )

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
                    self.write_valid_lock(cwd, target, str(consumer))
                elif phase == "frozen-replay":
                    with (cwd / "apm.lock.yaml").open("a", encoding="utf-8") as lock:
                        lock.write("# changed\n")

            with self.assertRaisesRegex(
                RuntimeError,
                "frozen replay changed apm.lock.yaml",
            ):
                validate_consumer.validate_consumer_in_directory(
                    str(consumer),
                    target,
                    consumer,
                    runner=fake_runner,
                )

    def test_cli_failure_emits_annotation_and_status(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        with mock.patch.object(
            validate_consumer,
            "validate_consumer",
            side_effect=RuntimeError("frozen replay failed"),
        ):
            with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
                with redirect_stdout(stdout):
                    with redirect_stderr(stderr):
                        status = validate_consumer.main(["--target", "agent-skills"])

        self.assertEqual(status, 1)
        self.assertIn(
            "::error title=Consumer validation failed::"
            "agent-skills: frozen replay failed",
            stderr.getvalue(),
        )
        self.assertIn("consumer_validation=failed", stdout.getvalue())

    def test_cli_success_writes_github_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output"

            with mock.patch.object(
                validate_consumer,
                "validate_consumer",
                return_value="a" * 64,
            ):
                status = validate_consumer.main(
                    [
                        "--target",
                        "agent-skills",
                        "--github-output",
                        str(output_path),
                    ]
                )

            self.assertEqual(status, 0)
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("consumer_target<<", content)
            self.assertIn("consumer_validation<<", content)
            self.assertIn("\npass\n", content)

    def test_remote_owner_repo_ref_source_is_forwarded_verbatim(self) -> None:
        source = "sergio-sisternes-epam/think#v0.1.0"
        with mock.patch.object(
            validate_consumer,
            "validate_consumer",
            return_value="a" * 64,
        ) as validator:
            status = validate_consumer.main(
                ["--source", source, "--target", "agent-skills"]
            )

        self.assertEqual(status, 0)
        validator.assert_called_once_with(source, "agent-skills", None)

    def test_remote_source_and_expected_revision_are_forwarded(self) -> None:
        source = "sergio-sisternes-epam/think#v0.1.0"
        revision = "a" * 40
        with mock.patch.object(
            validate_consumer,
            "validate_consumer",
            return_value="a" * 64,
        ) as validator:
            status = validate_consumer.main(
                [
                    "--source",
                    source,
                    "--target",
                    "agent-skills",
                    "--expected-revision",
                    revision,
                ]
            )

        self.assertEqual(status, 0)
        validator.assert_called_once_with(source, "agent-skills", revision)


if __name__ == "__main__":
    unittest.main()
