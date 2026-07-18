from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("compare_help_meta_harvest.py")
SPEC = importlib.util.spec_from_file_location("compare_help_meta_harvest", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class HelpMetaHarvestComparisonTests(unittest.TestCase):
    def test_content_delta_with_same_header_is_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            old = root / "old"
            new = root / "new"
            old.mkdir()
            new.mkdir()
            for name in MODULE.REQUIRED_FILES:
                (old / name).write_text("id,value\n1,old\n", encoding="utf-8")
                (new / name).write_text("id,value\n1,old\n", encoding="utf-8")
            (new / "HELP_COMMANDS.csv").write_text("id,value\n1,old\n2,new\n", encoding="utf-8")
            rows = MODULE.compare(old, new)
            changed = next(row for row in rows if row["file_name"] == "HELP_COMMANDS.csv")
            self.assertEqual(changed["status"], "CONTENT_CHANGED_COMPATIBLE_HEADER")
            self.assertEqual(changed["row_delta"], 1)

    def test_header_change_is_classified(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            old = root / "old"
            new = root / "new"
            old.mkdir()
            new.mkdir()
            for name in MODULE.REQUIRED_FILES:
                (old / name).write_text("id,value\n", encoding="utf-8")
                (new / name).write_text("id,value\n", encoding="utf-8")
            (new / "META_SYSCMD.csv").write_text("id,renamed\n", encoding="utf-8")
            rows = MODULE.compare(old, new)
            changed = next(row for row in rows if row["file_name"] == "META_SYSCMD.csv")
            self.assertEqual(changed["status"], "HEADER_CHANGED")


if __name__ == "__main__":
    unittest.main()
