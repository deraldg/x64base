"""Regression checks for the read-only MAN* catalog CLI."""

from __future__ import annotations

import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path


MANUALGEN_PATH = Path(__file__).resolve().parents[1] / "manualgen.py"
sys.path.insert(0, str(MANUALGEN_PATH.parent))
SPEC = importlib.util.spec_from_file_location("manualgen_entrypoint", MANUALGEN_PATH)
assert SPEC is not None and SPEC.loader is not None
MANUALGEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MANUALGEN)


def _write_minimal_dbf(path: Path, record_count: int) -> None:
    header = bytearray(32)
    header[0] = 0x03
    header[4:8] = struct.pack("<I", record_count)
    header[8:10] = struct.pack("<H", 33)
    header[10:12] = struct.pack("<H", 1)
    path.write_bytes(bytes(header) + b"\r")


class ManualCatalogCaseNormalizationTests(unittest.TestCase):
    def test_expected_tables_are_not_duplicated_as_extra_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            dbf_dir = (
                repo_root
                / "docs"
                / "manuals"
                / "developer"
                / "manualgen"
                / "accepted_catalogs"
                / "man_catalog_v1"
                / "dbf"
            )
            dbf_dir.mkdir(parents=True)

            expected = MANUALGEN._mdo256_expected_counts()
            for table, count in expected.items():
                _write_minimal_dbf(dbf_dir / f"{table}.dbf", count)

            _, rows = MANUALGEN._mdo256_table_rows(str(repo_root))

            self.assertEqual(len(rows), len(expected))
            self.assertTrue(all(row["pass"] == 1 for row in rows))
            self.assertFalse(any(row["failure_class"] == "EXTRA_MAN_DBF" for row in rows))


if __name__ == "__main__":
    unittest.main()
