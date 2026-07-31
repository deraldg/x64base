from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.controlled_acceptance_apply import (  # noqa: E402
    _final_after_bytes,
    _validate_authorization,
)


class ControlledAcceptanceApplyTests(unittest.TestCase):
    def test_authorization_binds_both_package_hashes(self) -> None:
        text = "\n".join(
            [
                "Decision: authorized for canonical apply.",
                "Plan run: `RUN`.",
                "Plan manifest SHA-256: `PLAN`.",
                "Mutation ledger SHA-256: `LEDGER`.",
                "Mutation rows authorized: 8.",
                "Required interpreter: Python 3.12.",
            ]
        )
        self.assertEqual([], _validate_authorization(text, "RUN", "PLAN", "LEDGER"))
        self.assertTrue(_validate_authorization(text, "RUN", "CHANGED", "LEDGER"))

    def test_planned_reader_record_becomes_final_only_during_apply(self) -> None:
        row = {
            "target": "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json",
            "action": "regenerate_on_apply",
        }
        planned = json.dumps(
            {"status": "PRIMARY_READER_CONTENT_ACCEPTANCE_PLANNED_POINTER_UNCHANGED"}
        ).encode()
        result = json.loads(
            _final_after_bytes(row, planned, "RUN", "auth.md", "2026-07-18T00:00:00Z")
        )
        self.assertEqual(
            "PRIMARY_READER_CONTENT_ACCEPTED_POINTER_UNCHANGED", result["status"]
        )
        self.assertEqual("RUN", result["acceptance_plan_run"])

    def test_appendix_record_drops_preview_instruction_during_apply(self) -> None:
        row = {
            "target": "docs/manuals/developer/manualgen/accepted_manifests/DOCFLUSH-20260716-001_APPENDIX_ACCEPTANCE_RECORD.md",
            "action": "generate_on_apply",
        }
        planned = (
            "Status: PLANNED_NOT_APPLIED\n\n"
            "Apply mode must replace this status with an execution result and retain the prior MDO-215 manifest as history.\n"
        ).encode()
        result = _final_after_bytes(
            row, planned, "RUN", "auth.md", "2026-07-18T00:00:00Z"
        ).decode()
        self.assertIn("Status: ACCEPTED_BY_AUTHORIZED_APPLY", result)
        self.assertNotIn("Apply mode must replace", result)


if __name__ == "__main__":
    unittest.main()
