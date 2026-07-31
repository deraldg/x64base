from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "staging"))

from execute_gate5_staging_rebuild import safe_path  # noqa: E402


class ExecuteGate5StagingRebuildTests(unittest.TestCase):
    def test_safe_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                safe_path(Path(temporary), "../outside.txt")

    def test_safe_path_accepts_nested_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "docs" / "manual.md"
            self.assertEqual(expected.resolve(), safe_path(root, "docs/manual.md"))

    def test_safe_path_requires_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                safe_path(Path(temporary), "missing.txt", must_exist=True)


if __name__ == "__main__":
    unittest.main()
