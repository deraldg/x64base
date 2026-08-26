from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "check_help_meta_harvest_freshness.py"
SPEC = importlib.util.spec_from_file_location("harvest_freshness", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class HarvestFreshnessTests(unittest.TestCase):
    def test_exact_content_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TABLE.csv"
            path.write_text("ID,NAME\n1,Alpha\n2,Beta\n", encoding="utf-8")
            result = MOD.compare_table(
                ["ID", "NAME"],
                [{"ID": "1", "NAME": "Alpha"}, {"ID": "2", "NAME": "Beta"}],
                path,
            )
            self.assertEqual("PASS", result["status"])
            self.assertEqual(0, result["mismatched_rows"])

    def test_same_count_with_changed_content_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TABLE.csv"
            path.write_text("ID,NAME\n1,Changed\n", encoding="utf-8")
            result = MOD.compare_table(
                ["ID", "NAME"], [{"ID": "1", "NAME": "Alpha"}], path
            )
            self.assertEqual("CONTENT_MISMATCH", result["status"])
            self.assertEqual(1, result["mismatched_rows"])
            self.assertEqual(2, result["first_mismatch_row"])

    def test_header_drift_fails_before_content_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TABLE.csv"
            path.write_text("ID,LABEL\n1,Alpha\n", encoding="utf-8")
            result = MOD.compare_table(
                ["ID", "NAME"], [{"ID": "1", "NAME": "Alpha"}], path
            )
            self.assertEqual("HEADER_MISMATCH", result["status"])
            self.assertEqual(0, result["header_match"])

    def test_manifest_must_bind_status_method_and_count(self) -> None:
        findings = MOD.manifest_findings(
            {
                "TABLE.csv": {
                    "required": "yes",
                    "current_status": "PENDING_EXPORT",
                    "row_count": "1",
                    "export_method": "",
                }
            },
            {"TABLE.csv": 2},
        )
        self.assertEqual(3, len(findings))
        self.assertTrue(any("current_status" in finding for finding in findings))
        self.assertTrue(any("export_method" in finding for finding in findings))
        self.assertTrue(any("row_count" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
