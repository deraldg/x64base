from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.gate4_acceptance_apply import (  # noqa: E402
    COMMAND_RECORD,
    FINALIZED_RECORDS,
    finalize_gate4_record,
    validate_gate4_authorization,
)


class Gate4AcceptanceApplyTests(unittest.TestCase):
    def test_authorization_binds_plan_ledger_rows_and_finalizations(self) -> None:
        payload = {
            "schema": "dottalk.manualgen.gate4_apply_authorization.v1",
            "decision": "AUTHORIZED_FOR_CANONICAL_APPLY",
            "plan_run": "RUN",
            "plan_manifest_sha256": "PLAN",
            "mutation_ledger_sha256": "LEDGER",
            "mutation_rows_authorized": 183,
            "required_interpreter": "Python 3.12",
            "apply_time_finalization_targets": sorted(FINALIZED_RECORDS),
        }
        self.assertEqual([], validate_gate4_authorization(payload, "RUN", "PLAN", "LEDGER"))
        payload["mutation_rows_authorized"] = 182
        self.assertTrue(validate_gate4_authorization(payload, "RUN", "PLAN", "LEDGER"))

    def test_command_record_is_finalized_only_during_apply(self) -> None:
        planned = json.dumps({"status": "ACCEPTED_PENDING_EXACT_GATE4_APPLY"}).encode()
        result = json.loads(
            finalize_gate4_record(COMMAND_RECORD, planned, "RUN", "auth.json", "2026-07-18T00:00:00Z")
        )
        self.assertEqual("ACCEPTED_COMMAND_REFERENCE", result["status"])
        self.assertEqual("auth.json", result["authorization_record"])


if __name__ == "__main__":
    unittest.main()
