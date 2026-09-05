from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

import ci_output


class CiOutputTests(unittest.TestCase):
    def read_outputs(self, path: Path) -> dict[str, str]:
        lines = path.read_text(encoding="utf-8").splitlines()
        values = {}
        index = 0
        while index < len(lines):
            key, delimiter = lines[index].split("<<", 1)
            end = lines.index(delimiter, index + 1)
            values[key] = "\n".join(lines[index + 1 : end])
            index = end + 1
        return values

    def test_multiline_output_cannot_inject_another_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "github-output"
            value = "first\ninjected=value\nghadelimiter_not_the_random_value"

            ci_output.write_github_outputs(output, {"safe_value": value})

            self.assertEqual(self.read_outputs(output), {"safe_value": value})

    def test_invalid_output_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "github-output"

            with self.assertRaisesRegex(ValueError, "invalid GitHub output name"):
                ci_output.write_github_outputs(output, {"bad name": "value"})

    def test_annotation_properties_escape_colon_and_comma(self) -> None:
        stderr = StringIO()

        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
            with redirect_stderr(stderr):
                ci_output.emit_error("message", title="a:b,c")

        self.assertIn("::error title=a%3Ab%2Cc::message", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
