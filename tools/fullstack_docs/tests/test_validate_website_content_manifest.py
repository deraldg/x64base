from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "fullstack_docs" / "validate_website_content_manifest.py"
SPEC = importlib.util.spec_from_file_location("validate_website_content_manifest", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class WebsiteContentManifestTests(unittest.TestCase):
    def test_exact_classification_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "content"
            (content / "docs").mkdir(parents=True)
            (content / "docs" / "one.mdx").write_text("one", encoding="utf-8")
            (content / "two.mdx").write_text("two", encoding="utf-8")
            manifest = root / "manifest.yaml"
            manifest.write_text(
                """classes:
  generated: {pages: [docs/one]}
  derived: {pages: []}
  maintained: {pages: [two]}
  maintained_current: {pages: []}
  reported: {pages: []}
  static: {pages: []}
totals: {generated: 1, derived: 0, maintained: 1, maintained_current: 0, reported: 0, static: 0, total: 2}
publication_check:
  required_gates:
    - {id: content_inventory, mode: hard}
    - {id: fullstack_publication_entry, mode: hard}
    - {id: function_catalog, mode: hard}
    - {id: error_codes, mode: hard}
    - {id: locales, mode: hard}
""",
                encoding="utf-8",
            )
            self.assertEqual([], MODULE.validate(manifest, content))

    def test_missing_duplicate_and_bad_total_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = root / "content"
            content.mkdir()
            (content / "one.mdx").write_text("one", encoding="utf-8")
            manifest = root / "manifest.yaml"
            manifest.write_text(
                """classes:
  generated: {pages: [ghost, ghost]}
  derived: {pages: []}
  maintained: {pages: []}
  maintained_current: {pages: []}
  reported: {pages: []}
  static: {pages: []}
totals: {generated: 1, derived: 0, maintained: 0, maintained_current: 0, reported: 0, static: 0, total: 1}
publication_check:
  required_gates:
    - {id: content_inventory, mode: advisory}
""",
                encoding="utf-8",
            )
            findings = MODULE.validate(manifest, content)
            self.assertTrue(any("duplicate" in finding for finding in findings))
            self.assertTrue(any("missing from manifest" in finding for finding in findings))
            self.assertTrue(any("missing on disk" in finding for finding in findings))
            self.assertTrue(any("total generated" in finding for finding in findings))
            self.assertTrue(any("must be hard" in finding for finding in findings))
            self.assertTrue(any("missing publication gates" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
