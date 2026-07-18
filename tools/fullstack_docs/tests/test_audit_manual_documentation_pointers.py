from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/audit_manual_documentation_pointers.py"
SPEC = importlib.util.spec_from_file_location("audit_manual_documentation_pointers", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ManualPointerAuditTests(unittest.TestCase):
    def test_markdown_heading_count_counts_only_real_headings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manual.md"
            path.write_text(
                "# Manual\n\n## Section\nnot # a heading\n### Subsection\n####### Too deep\n",
                encoding="utf-8",
            )
            self.assertEqual(3, MOD.markdown_heading_count(path))


if __name__ == "__main__":
    unittest.main()
