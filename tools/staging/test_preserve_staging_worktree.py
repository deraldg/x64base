from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "staging"))

from preserve_staging_worktree import parse_porcelain_z, safe_file  # noqa: E402


class PreserveStagingWorktreeTests(unittest.TestCase):
    def test_porcelain_z_keeps_status_and_spaces(self) -> None:
        rows = parse_porcelain_z(b" M docs/a file.md\0?? new.txt\0")
        self.assertEqual(
            [
                {"status": " M", "path": "docs/a file.md"},
                {"status": "??", "path": "new.txt"},
            ],
            rows,
        )

    def test_safe_file_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                safe_file(root, "../outside.txt")

    def test_safe_file_accepts_nested_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "docs" / "file.md"
            path.parent.mkdir()
            path.write_text("ok", encoding="utf-8")
            self.assertEqual(path.resolve(), safe_file(root, "docs/file.md"))


if __name__ == "__main__":
    unittest.main()
