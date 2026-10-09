# AI Portal Identifier Normalization Status

Generated from the typed identifier model and maintained authorities. Do not hand-edit.

## Inventory

| Class | Records |
| --- | ---: |
| `identifier_classes` | 8 |
| `projects` | 22 |
| `aif_intake_rows` | 160 |
| `aif_claims` | 95 |
| `rulings` | 35 |
| `runs` | 20 |
| `work_items` | 17 |
| `proofs` | 74 |

## Compatibility observations

- `aif_claim_backfill`: intake_without_claim=65, claim_without_intake=0
- `legacy_ticket_crosswalk`: external_ticket_id=2, lane_id=15
- `run_report_compatibility`: report_ids_in_run_id_field=20
- `lane_references`: task_lanes=13, run_lanes=24, task_lanes_without_claim=10, run_lanes_without_intake=0

## Findings

- `AIF-111` [claim_ledger]: claim file is present but not tracked: coordination/aif/AIF-111.claim
- `AIF-131` [claim_ledger]: claim file is present but not tracked: coordination/aif/AIF-131.claim
- `AIF-134` [claim_ledger]: claim file is present but not tracked: coordination/aif/AIF-134.claim
- `AIF-135` [claim_ledger]: claim file is present but not tracked: coordination/aif/AIF-135.claim
- `AIF-136` [claim_ledger]: claim file is present but not tracked: coordination/aif/AIF-136.claim
- `AIF-163` [claim_ledger]: claim file is present but not tracked: coordination/aif/AIF-163.claim

## Boundary

Legacy fields are classified, not rewritten. Backfill gaps remain advisory until an owner ruling promotes them to a hard gate.
