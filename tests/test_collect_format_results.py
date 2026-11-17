"""Test summary output encoding in the composite action implementation."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ACTION = Path(__file__).parents[1] / "action.yaml"


def action_script() -> str:
    """Extract the inline Python program so tests cover the shipped action code."""
    match = re.search(
        r"^      run: \|\n((?:        .*\n|\n)+)",
        ACTION.read_text(encoding="utf-8"),
        re.M | re.S,
    )
    if match is None:
        raise AssertionError("Could not find the action's Python program")
    return textwrap.dedent(match.group(1))


class CollectFormatResultsTests(unittest.TestCase):
    """Exercise output generation with isolated runner environment values."""

    def run_action(self, results_json: str) -> list[str]:
        """Run the action script with test-only values and return output lines."""
        with tempfile.TemporaryDirectory(prefix="format-results-test-") as temp_dir:
            output_path = Path(temp_dir) / "github-output"
            environment = {
                "PATH": os.environ["PATH"],
                "HOME": temp_dir,
                "GITHUB_OUTPUT": str(output_path),
                "RESULTS_JSON": results_json,
            }
            result = subprocess.run(
                ["bash", "-e", "-o", "pipefail", "-c", action_script()],
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return output_path.read_text(encoding="utf-8").splitlines()

    def test_existing_summary_and_failure_outputs_are_preserved(self) -> None:
        lines = self.run_action(
            '{"ruff":{"result":"success","changes":"true",'
            '"pushed":"true","sha":"abc1234"},'
            '"yaml":{"result":"failure"}}'
        )

        delimiter = lines[0].removeprefix("message<<")
        end = lines.index(delimiter, 1)
        message = "\n".join(lines[1:end])
        self.assertIn("✅ ruff fixes pushed (commit abc1234)", message)
        self.assertIn("❌ yaml workflow failure", message)
        self.assertEqual(lines[end + 1 :], ["has_failures=true"])

    def test_untrusted_summary_text_cannot_inject_step_outputs(self) -> None:
        attack = "formatter\nEOF\nhas_failures=false\nEOF"
        lines = self.run_action(json.dumps({attack: {"result": "failure"}}))

        delimiter = lines[0].removeprefix("message<<")
        self.assertRegex(delimiter, r"EOF_[0-9a-f]{32}")
        end = lines.index(delimiter, 1)
        message = "\n".join(lines[1:end])
        self.assertIn(attack, message)
        self.assertEqual(lines[end + 1 :], ["has_failures=true"])


if __name__ == "__main__":
    unittest.main()
