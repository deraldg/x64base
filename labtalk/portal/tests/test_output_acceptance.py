from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


PORTAL_ROOT = Path(__file__).resolve().parents[1]
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from labtalk_portal import PortalItem, output_acceptance_issues, write_transcript  # noqa: E402


def item(**data: object) -> PortalItem:
    return PortalItem(
        section_id="portal.test",
        section_label="Test",
        item_id="probe.test",
        label="Test probe",
        kind="dottalk_script",
        data=dict(data),
    )


class OutputAcceptanceTests(unittest.TestCase):
    def test_accepts_required_markers(self) -> None:
        probe = item(required_output_patterns=["BEGIN", "END"])
        self.assertEqual(output_acceptance_issues(probe, "BEGIN\nEND\n", ""), [])

    def test_rejects_missing_required_marker(self) -> None:
        probe = item(required_output_patterns=["BEGIN", "END"])
        self.assertEqual(
            output_acceptance_issues(probe, "BEGIN\n", ""),
            ["required output missing: END"],
        )

    def test_rejects_unknown_command_even_when_process_can_succeed(self) -> None:
        probe = item()
        issues = output_acceptance_issues(
            probe,
            "DOTSCRIPT: sample.dts:4: Unknown command: MADEUP THING\n",
            "",
        )
        self.assertEqual(issues, ["rejected output present: Unknown command:"])

    def test_rejects_configured_pattern_case_insensitively(self) -> None:
        probe = item(reject_output_patterns=["missing expected readback"])
        issues = output_acceptance_issues(probe, "Missing Expected Readback", "")
        self.assertIn("rejected output present: missing expected readback", issues)

    def test_default_rejections_can_be_disabled_for_negative_tests(self) -> None:
        probe = item(use_default_dotscript_reject_patterns=False)
        self.assertEqual(output_acceptance_issues(probe, "Unknown command: EXPECTED", ""), [])

    def test_invalid_pattern_configuration_is_rejected(self) -> None:
        probe = item(required_output_patterns="BEGIN")
        with self.assertRaisesRegex(ValueError, "required_output_patterns"):
            output_acceptance_issues(probe, "BEGIN", "")

    def test_transcript_has_one_final_newline_and_explicit_empty_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transcript = write_transcript(
                item(proof_output_dir=tmp),
                ["dottalkpp", "--script", "probe.dts"],
                0,
                "probe output\n",
                "",
            )
            text = transcript.read_text(encoding="utf-8")

        self.assertTrue(text.endswith("STDERR\n======\n(none)\n"))
        self.assertFalse(text.endswith("\n\n"))


if __name__ == "__main__":
    unittest.main()
