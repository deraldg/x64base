from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.gate5_development_apply import (  # noqa: E402
    COMMAND_RECORD,
    FINALIZED_RECORDS,
    finalize_gate5_record,
    validate_gate5_authorization,
)


class Gate5DevelopmentApplyTests(unittest.TestCase):
    def test_authorization_binds_plan_counts_boundaries_and_finalizations(self) -> None:
        payload = {
            "schema": "dottalk.manualgen.gate5_development_apply_authorization.v1",
            "decision": "AUTHORIZED_FOR_DEVELOPMENT_DOCUMENTATION_APPLY",
            "plan_run": "RUN",
            "plan_manifest_sha256": "PLAN",
            "mutation_ledger_sha256": "LEDGER",
            "mutation_rows_authorized": 25,
            "create_rows_authorized": 19,
            "replace_rows_authorized": 6,
            "required_interpreter": "Python 3.12",
            "apply_time_finalization_targets": sorted(FINALIZED_RECORDS),
            "scope": {
                "development_documentation_apply": "AUTHORIZED",
                "source_staging_mutation": "NOT_AUTHORIZED",
                "git_index_commit_push": "NOT_AUTHORIZED",
                "website_mutation": "NOT_AUTHORIZED",
            },
        }
        self.assertEqual([], validate_gate5_authorization(payload, "RUN", "PLAN", "LEDGER"))
        payload["scope"]["source_staging_mutation"] = "AUTHORIZED"
        self.assertTrue(validate_gate5_authorization(payload, "RUN", "PLAN", "LEDGER"))

    def test_command_record_is_finalized_only_during_apply(self) -> None:
        planned = json.dumps(
            {"status": "GATE5_SUPPLEMENTAL_SOURCE_PLAN_PENDING_APPLY", "page_count": 183}
        ).encode()
        result = json.loads(
            finalize_gate5_record(
                COMMAND_RECORD,
                planned,
                "PLAN",
                "APPLY",
                "auth.json",
                "2026-07-18T00:00:00Z",
            )
        )
        self.assertEqual("ACCEPTED_COMMAND_REFERENCE_183_PAGES", result["status"])
        self.assertEqual("auth.json", result["gate5_acceptance_authorization_record"])
        self.assertEqual("APPLY", result["gate5_apply_run"])


if __name__ == "__main__":
    unittest.main()
