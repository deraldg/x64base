from __future__ import annotations

import sys
import unittest
from pathlib import Path


PORTAL_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import labtalk_portal  # noqa: E402


class AiReportAuditIntegrationTests(unittest.TestCase):
    def test_portal_truth_audit_includes_clean_ai_report_gate(self) -> None:
        audit = labtalk_portal.audit_portal()

        self.assertIn("ai_report_audit", audit)
        self.assertEqual(audit["ai_report_audit"]["schema"], "ai-report-audit-v1")
        self.assertEqual(audit["ai_report_audit"]["finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
