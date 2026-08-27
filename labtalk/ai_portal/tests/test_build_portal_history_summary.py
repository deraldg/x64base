from __future__ import annotations

import sys
import unittest
from pathlib import Path


LABTALK_ROOT = Path(__file__).resolve().parents[2]
if str(LABTALK_ROOT) not in sys.path:
    sys.path.insert(0, str(LABTALK_ROOT))

from ai_portal import build_portal_history_summary as builder  # noqa: E402


class PortalHistorySummaryTests(unittest.TestCase):
    def manifest(self, state: str = "approved") -> dict[str, object]:
        return {
            "ruling_state": state,
            "physical_action": "none_authorized",
            "items": [{
                "memory_id": "memory.file." + "1" * 20,
                "portal_summary": "Historical summary.",
                "source_uri": "labtalk/ai_portal/history.md",
                "expected_sha256": "a" * 64,
                "expected_size_bytes": 12,
                "authority_class": "reviewed_derivative",
                "sensitivity": "development_only",
                "lineage_note": "No supersession declared.",
            }],
        }

    def test_summary_is_bounded_and_resolves_exact_body_and_hash(self) -> None:
        text = builder.render_summary(self.manifest())
        self.assertIn("trigger.portal_history", text)
        self.assertIn("labtalk/ai_portal/history.md", text)
        self.assertIn("a" * 64, text)
        self.assertIn("authorizes no copy, move, deletion", text)

    def test_unapproved_manifest_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "approved owner ruling"):
            builder.render_summary(self.manifest("awaiting_owner_ruling"))


if __name__ == "__main__":
    unittest.main()
