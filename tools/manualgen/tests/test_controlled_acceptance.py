from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.controlled_acceptance import (  # noqa: E402
    EXPECTED_REVIEW,
    _heading_count,
    validate_pointer_audit,
)


class ControlledAcceptancePlanTests(unittest.TestCase):
    def test_exact_green_pointer_audit_is_required(self) -> None:
        payload = {
            "schema": "dottalk.fullstack.manual_pointer_audit.v1",
            "summary": {"pass": 21, "review": 1, "fail": 0},
            "checks": [{"check_id": EXPECTED_REVIEW, "status": "REVIEW"}],
        }
        self.assertEqual([], validate_pointer_audit(payload))

    def test_unexpected_review_fails_closed(self) -> None:
        payload = {
            "schema": "dottalk.fullstack.manual_pointer_audit.v1",
            "summary": {"pass": 21, "review": 1, "fail": 0},
            "checks": [{"check_id": "UNEXPECTED", "status": "REVIEW"}],
        }
        self.assertTrue(validate_pointer_audit(payload))

    def test_heading_count_matches_pointer_audit_contract(self) -> None:
        text = "# Manual\n## Section\nnot # heading\n####### invalid\n### Child\n"
        self.assertEqual(3, _heading_count(text))


if __name__ == "__main__":
    unittest.main()
