from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.gate5_source_gap import _status_decisions  # noqa: E402


class Gate5SourceGapTests(unittest.TestCase):
    def test_status_occurrences_collapse_to_four_logical_decisions(self) -> None:
        rows = [
            {"title": "Navigation, Browsing, and Search", "status": "DRAFT / REVIEW_REQUIRED", "path": "nav.md"},
            {"title": "Appendix A", "status": "DRAFT / REVIEW_REQUIRED", "path": "aggregate.md"},
            {"title": "Appendix A", "status": "DRAFT / REVIEW_REQUIRED", "path": "appendix.md"},
            {"title": "Appendix B", "status": "DRAFT / REVIEW_REQUIRED", "path": "aggregate.md"},
            {"title": "Appendix B", "status": "DRAFT / REVIEW_REQUIRED", "path": "appendix.md"},
            {"title": "Appendix C", "status": "DRAFT / REVIEW_REQUIRED", "path": "aggregate.md"},
            {"title": "Appendix C", "status": "DRAFT / REVIEW_REQUIRED", "path": "appendix.md"},
        ]
        decisions = _status_decisions(rows)
        self.assertEqual(4, len(decisions))
        navigation = next(row for row in decisions if row["title"].startswith("Navigation"))
        self.assertEqual("CONDITIONAL_APPROVE_AFTER_19_PAGE_ACCEPTANCE", navigation["proposed_decision"])
        self.assertEqual(3, sum(row["proposed_decision"] == "HOLD_REVIEW_REQUIRED" for row in decisions))


if __name__ == "__main__":
    unittest.main()
