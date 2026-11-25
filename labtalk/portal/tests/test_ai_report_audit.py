from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


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

    def test_a_missing_launcher_blocks_but_a_missing_historical_proof_is_advisory(self) -> None:
        launcher = labtalk_portal.PortalItem(
            "launchers", "Launchers", "launch.missing", "Launcher", "powershell_launcher",
            {"path": "path-that-does-not-exist/test.ps1"},
        )
        proof = labtalk_portal.PortalItem(
            "proofs", "Proofs", "proof.missing", "Evidence", "proof",
            {"path": "path-that-does-not-exist/history.md"},
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(labtalk_portal, "load_portal_items", return_value=([], [launcher, proof])),
            mock.patch.object(labtalk_portal, "audit_ai_report_closeouts", return_value={"finding_count": 0}),
            mock.patch.object(sys, "argv", ["labtalk_portal.py", "--audit-check"]),
            mock.patch.object(labtalk_portal, "write_portal_audit") as writer,
            contextlib.redirect_stdout(stdout),
        ):
            self.assertEqual(labtalk_portal.main(), 2)
            writer.assert_not_called()
        self.assertIn("1 blocker(s), 1 advisory", stdout.getvalue())
        self.assertIn("BLOCKER launch.missing missing path:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
