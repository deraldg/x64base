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
        # Wording-independent: the v0 column is `current_status`, the v1 column
        # is `status`, and the finding now names whichever it read. The BEHAVIOUR
        # under test -- PENDING_EXPORT is rejected -- is unchanged.
        self.assertTrue(any("status" in finding for finding in findings))
        self.assertTrue(any("export_method" in finding for finding in findings))
        self.assertTrue(any("row_count" in finding for finding in findings))

    def test_v1_manifest_schema_is_accepted(self) -> None:
        """v1 uses `status` and carries no `required` column."""
        findings = MOD.manifest_findings(
            {
                "TABLE.csv": {
                    "target_csv": "TABLE.csv",
                    "status": "EXPORTED",
                    "row_count": "2",
                    "sha256": "ABC",
                    "source": "HELP/META current",
                    "export_method": "DOTSCRIPT+EXPORT CSV",
                }
            },
            {"TABLE.csv": 2},
        )
        self.assertEqual([], findings)

    def test_carried_stale_is_not_a_finding(self) -> None:
        """CARRIED_STALE_MAY is the honest label, not a defect.

        The sanctioned producer writes it for the four META_* tables whose
        sources are not current. Demanding EXPORTED flagged them for being
        truthful. Its row_count describes the carried file, not the live source,
        so that comparison is skipped too.
        """
        findings = MOD.manifest_findings(
            {
                "TABLE.csv": {
                    "target_csv": "TABLE.csv",
                    "status": "CARRIED_STALE_MAY",
                    "row_count": "12",
                    "export_method": "(carried forward -- source not yet current)",
                }
            },
            {"TABLE.csv": 999},
        )
        self.assertEqual([], findings)

    def test_memo_columns_are_excluded_from_comparison(self) -> None:
        """The reference cannot render memo, so it must not judge memo.

        Regression guard for the E5 inversion measured 2026-09-02: the check
        passed the memo-BLANK harvest and failed the memo-BEARING one.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TABLE.csv"
            path.write_text("ID,NOTES\n1,real memo text\n", encoding="utf-8")
            result = MOD.compare_table(
                ["ID", "NOTES"],
                [{"ID": "1", "NOTES": ""}],          # reference: memo blanked
                path,
                memo_columns=frozenset({"NOTES"}),
            )
            self.assertEqual("PASS", result["status"])
            self.assertEqual(1, result["memo_populated_rows"])
            self.assertIn("RESOLVED", result["memo_rendering"])

    def test_non_memo_difference_still_fails(self) -> None:
        """Excluding memo must not make the check permissive."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TABLE.csv"
            path.write_text("ID,NOTES\n2,memo\n", encoding="utf-8")
            result = MOD.compare_table(
                ["ID", "NOTES"],
                [{"ID": "1", "NOTES": ""}],
                path,
                memo_columns=frozenset({"NOTES"}),
            )
            self.assertEqual("CONTENT_MISMATCH", result["status"])

    def test_numeric_padding_is_not_a_content_difference(self) -> None:
        """The engine preserves DBF fixed-width padding; dbfread strips it."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "TABLE.csv"
            path.write_text("ID,NAME\n       337,Alpha\n", encoding="utf-8")
            result = MOD.compare_table(
                ["ID", "NAME"], [{"ID": "337", "NAME": "Alpha"}], path
            )
            self.assertEqual("PASS", result["status"])

    def test_recode_recovers_utf8_from_latin1_mojibake(self) -> None:
        """dbfread decodes latin1; the store holds UTF-8.

        NO LITERALS. This file is ASCII-only by house rule and the subject under
        test is precisely non-ASCII bytes, so every character is built with
        chr(). U+2014 EM DASH is E2 80 94 in UTF-8; read back as latin1 those
        bytes are U+00E2 U+0080 U+0094, which is the mojibake this recovers.
        """
        em_dash = chr(0x2014)
        mojibake = "a " + chr(0xE2) + chr(0x80) + chr(0x94) + " b"
        self.assertEqual("a " + em_dash + " b", MOD._recode(mojibake))
        self.assertEqual("plain ascii", MOD._recode("plain ascii"))
        # Lone 0xFF is not valid UTF-8: returned unchanged, not mangled.
        self.assertEqual(chr(0xFF), MOD._recode(chr(0xFF)))


if __name__ == "__main__":
    unittest.main()
