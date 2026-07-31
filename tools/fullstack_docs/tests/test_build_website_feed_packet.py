from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/fullstack_docs/build_website_feed_packet.py"
SPEC = importlib.util.spec_from_file_location("build_website_feed_packet", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class WebsiteFeedPacketTests(unittest.TestCase):
    def test_route_contract_is_narrow_and_complete(self) -> None:
        rows = MOD.ROUTE_SPECS
        self.assertEqual(11, len(rows))
        self.assertEqual(2, sum(row["action"] == "CREATE" for row in rows))
        self.assertEqual(8, sum(row["action"] == "UPDATE" for row in rows))
        self.assertEqual(1, sum(row["action"] == "REPLACE" for row in rows))
        self.assertEqual(len(rows), len({row["site_path"] for row in rows}))
        self.assertTrue(all(row["route"].startswith("/") for row in rows))

    def test_only_reviewed_proof_labels_are_exported(self) -> None:
        allowed = {"manual-reviewed", "generated-reviewed", "help-catalog-evidenced"}
        self.assertEqual(set(), {row["proof_label"] for row in MOD.ROUTE_SPECS} - allowed)

    def test_markdown_counts_real_headings_and_lines(self) -> None:
        data = b"# One\ntext\n## Two\n"
        self.assertEqual((3, 2), MOD._count_markdown(data))

    def test_payload_paths_are_repository_relative(self) -> None:
        for row in MOD.ROUTE_SPECS:
            self.assertNotIn(":", row["site_path"])
            self.assertNotIn("\\", row["site_path"])
            self.assertFalse(row["site_path"].startswith("/"))


if __name__ == "__main__":
    unittest.main()
