from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.gate5_development_plan import (  # noqa: E402
    _append_manifest_entries,
    _parse_existing_index,
    _render_accepted_index,
)
from manualgen_lib.gate5_source_gap import PROMOTE_ADDITIONS  # noqa: E402


class Gate5DevelopmentPlanTests(unittest.TestCase):
    def test_index_round_trip_keeps_attention_and_links(self) -> None:
        rows = [
            {
                "label": "BETA",
                "filename": "beta.md",
                "attention": True,
                "topic_key": "DOT|BETA",
                "status": "partial",
                "evidence_rows": 2,
            },
            {
                "label": "ALPHA",
                "filename": "alpha.md",
                "attention": False,
                "topic_key": "DOT|ALPHA",
                "status": "supported",
                "evidence_rows": 3,
            },
        ]
        rendered = _render_accepted_index(rows)
        parsed = _parse_existing_index(rendered)
        self.assertEqual(["ALPHA", "BETA"], [row["label"] for row in parsed])
        self.assertFalse(parsed[0]["attention"])
        self.assertTrue(parsed[1]["attention"])

    def test_manifest_entries_are_added_once(self) -> None:
        first = _append_manifest_entries("PROMOTE.manifest\n")
        second = _append_manifest_entries(first)
        self.assertEqual(first, second)
        for entry in PROMOTE_ADDITIONS:
            self.assertEqual(1, first.splitlines().count(entry))


if __name__ == "__main__":
    unittest.main()
