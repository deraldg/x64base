from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "manualgen"))

from manualgen_lib.gate4_acceptance_apply import (  # noqa: E402
    CANONICAL_RECORD,
    COMMAND_RECORD,
    FINALIZED_RECORDS,
    PRIMARY_RECORD,
    PUBLICATION,
    _validate_target_set,
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
        self.assertEqual(
            [], validate_gate4_authorization(payload, "RUN", "PLAN", "LEDGER", 183)
        )
        payload["mutation_rows_authorized"] = 182
        self.assertTrue(
            validate_gate4_authorization(payload, "RUN", "PLAN", "LEDGER", 183)
        )

    def test_command_record_is_finalized_only_during_apply(self) -> None:
        planned = json.dumps(
            {
                "status": "ACCEPTED_PENDING_EXACT_GATE4_APPLY",
                "page_count": 183,
            }
        ).encode()
        result = json.loads(
            finalize_gate4_record(COMMAND_RECORD, planned, "RUN", "auth.json", "2026-07-18T00:00:00Z")
        )
        self.assertEqual("ACCEPTED_COMMAND_REFERENCE_183_PAGES", result["status"])
        self.assertEqual("auth.json", result["authorization_record"])

    def test_refresh_target_set_can_omit_unchanged_reader_and_sections(self) -> None:
        rows = [
            {
                "target": f"{PUBLICATION}/command_reference_v1/commands/page-{index}.md",
                "operation": "REPLACE",
            }
            for index in range(164)
        ]
        rows.extend(
            [
                {
                    "target": f"{PUBLICATION}/command_reference_v1/README.md",
                    "operation": "REPLACE",
                },
                {"target": PRIMARY_RECORD, "operation": "REPLACE"},
                {"target": CANONICAL_RECORD, "operation": "REPLACE"},
                {"target": COMMAND_RECORD, "operation": "REPLACE"},
            ]
        )
        counts = {
            "planned_mutation_rows": 168,
            "planned_create_rows": 0,
            "planned_replace_rows": 168,
            "command_pages": 164,
            "section_status_files": 0,
        }
        self.assertEqual([], _validate_target_set(rows, counts))


if __name__ == "__main__":
    unittest.main()
