from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/audit_manual_publication_readiness.py"
SPEC = importlib.util.spec_from_file_location("audit_manual_publication_readiness", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class ManualPublicationReadinessTests(unittest.TestCase):
    def test_markdown_destinations_exclude_images(self) -> None:
        text = "[manual](manual.md) ![diagram](diagram.png) [web](https://example.com)"
        self.assertEqual(["manual.md", "https://example.com"], MOD.markdown_destinations(text))

    def test_broken_local_links_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            reader = Path(temp) / "manual.md"
            reader.write_text("# Manual\n", encoding="utf-8")
            (Path(temp) / "present.md").write_text("ok\n", encoding="utf-8")
            self.assertEqual(
                ["missing.md"],
                MOD.broken_local_links(reader, ["present.md", "missing.md", "#anchor"]),
            )


if __name__ == "__main__":
    unittest.main()
