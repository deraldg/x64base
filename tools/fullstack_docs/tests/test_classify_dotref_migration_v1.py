from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/classify_dotref_migration_v1.py"
SPEC = importlib.util.spec_from_file_location("classify_dotref_migration_v1", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class DotrefMigrationTests(unittest.TestCase):
    def test_field_and_member_classification_is_explicit(self) -> None:
        current = [
            SimpleNamespace(name="BAR", syntax="BAR", summary="Old bar.", supported=True),
            SimpleNamespace(name="OLD", syntax="OLD", summary="Old only.", supported=True),
        ]
        candidate = [
            {"NAME": "BAR", "SYNTAX": "BAR <x>", "SUMMARY": "Old bar.", "SUPPORTED": "T"},
            {"NAME": "NEW", "SYNTAX": "NEW", "SUMMARY": "New only.", "SUPPORTED": "T"},
        ]
        rows = MOD.classify(current, candidate)
        keyed = {(row["NAME"], row["FIELD"]): row for row in rows}
        self.assertEqual("FIELD_REVIEW_REQUIRED", keyed[("BAR", "SYNTAX")]["CLASSIFICATION"])
        self.assertEqual("ALIGNED", keyed[("BAR", "SUMMARY")]["CLASSIFICATION"])
        self.assertEqual("HEADER_ONLY_REVIEW_REQUIRED", keyed[("OLD", "MEMBER")]["CLASSIFICATION"])
        self.assertEqual("NEW_IDENTITY_REVIEW_REQUIRED", keyed[("NEW", "MEMBER")]["CLASSIFICATION"])

    def test_fold_projection_uses_ordered_syntax_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            assembly = Path(temp)
            candidate = assembly / "candidate"
            candidate.mkdir()
            self._write_csv(candidate / "sysref_candidate.csv", [
                "REF_ID", "CAN_NAME", "SUPPORTED", "ACTIVE",
            ], [{"REF_ID": "R1", "CAN_NAME": "FOO", "SUPPORTED": "T", "ACTIVE": "T"}])
            self._write_csv(candidate / "sysrefline_candidate.csv", [
                "REF_ID", "KIND", "ORDINAL", "TEXT", "ACTIVE",
            ], [
                {"REF_ID": "R1", "KIND": "SYNTAX", "ORDINAL": "2", "TEXT": "FOO STATUS", "ACTIVE": "T"},
                {"REF_ID": "R1", "KIND": "SUMMARY", "ORDINAL": "1", "TEXT": "Foo summary.", "ACTIVE": "T"},
                {"REF_ID": "R1", "KIND": "SYNTAX", "ORDINAL": "1", "TEXT": "FOO", "ACTIVE": "T"},
            ])
            rows = MOD.fold_projection(assembly)
            self.assertEqual("FOO | FOO STATUS", rows[0]["SYNTAX"])
            self.assertEqual("Foo summary.", rows[0]["SUMMARY"])

    def test_output_directory_reuse_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            out = root / "out"
            out.mkdir()
            self.assertEqual(2, MOD.main([
                "--root", str(root), "--assembly", "assembly",
                "--header", "include/dotref.hpp", "--out", "out", "--report-only",
            ]))

    @staticmethod
    def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
