from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/build_reference_identity_inventory.py"
SPEC = importlib.util.spec_from_file_location("build_reference_identity_inventory", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class ReferenceIdentityUsageCatalogTests(unittest.TestCase):
    def test_srcusage_uses_block_and_file_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            usage = root / "SRCUSAGE_IMPORT.csv"
            write_csv(usage, ["USAGEID", "BLOCKID", "FILEID", "COMMAND"], [
                {"USAGEID": "1", "BLOCKID": "9", "FILEID": "2", "COMMAND": "ENDIF"},
            ])
            write_csv(root / "SRCFILE_IMPORT.csv", ["FILEID", "RELPATH"], [
                {"FILEID": "2", "RELPATH": "src/cli/cmd_if.cpp"},
            ])
            write_csv(root / "SRCBLOCK_IMPORT.csv", ["BLOCKID", "STARTLN"], [
                {"BLOCKID": "9", "STARTLN": "154"},
            ])
            self.assertEqual([{
                "identity": "ENDIF", "source": "src/cli/cmd_if.cpp", "line": "154",
            }], MOD.usage_items(usage))

    def test_legacy_srcfile_remains_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SRCFILE_IMPORT.csv"
            write_csv(path, ["RELPATH", "FIRST_HDR", "DET_CMD"], [
                {"RELPATH": "src/cli/cmd_if.cpp", "FIRST_HDR": "1", "DET_CMD": "IF"},
            ])
            self.assertEqual([{
                "identity": "IF", "source": "src/cli/cmd_if.cpp", "line": "1",
            }], MOD.usage_items(path))


if __name__ == "__main__":
    unittest.main()
