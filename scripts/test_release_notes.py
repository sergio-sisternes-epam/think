from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import release_notes


ROOT = Path(__file__).resolve().parents[1]


class ReleaseNotesTests(unittest.TestCase):
    def test_extracts_curated_release_without_link_definitions(self) -> None:
        notes = release_notes.release_notes("0.1.0", ROOT)

        self.assertIn("nine\n  agent harnesses", notes)
        self.assertIn("consumer-owned frozen locks", notes)
        self.assertNotIn("separately approved", notes)
        self.assertNotIn("[Unreleased]:", notes)

    def test_missing_release_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "release notes not found"):
            release_notes.release_notes("9.9.9", ROOT)

    def test_cli_writes_release_notes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "notes.md"

            status = release_notes.main(
                ["--version", "0.1.0", "--output", str(output)],
                ROOT,
            )

            self.assertEqual(status, 0)
            self.assertTrue(output.read_text(encoding="utf-8").endswith("\n"))


if __name__ == "__main__":
    unittest.main()
