# AI Portal Identifier Normalization Status

Generated from the typed identifier model and maintained authorities. Do not hand-edit.

## Inventory

| Class | Records |
| --- | ---: |
| `identifier_classes` | 8 |
| `projects` | 21 |
| `aif_intake_rows` | 130 |
| `aif_claims` | 65 |
| `rulings` | 20 |
| `runs` | 20 |
| `work_items` | 17 |
| `proofs` | 74 |

## Compatibility observations

- `aif_claim_backfill`: intake_without_claim=65, claim_without_intake=0
- `legacy_ticket_crosswalk`: external_ticket_id=3, lane_id=14
- `run_report_compatibility`: report_ids_in_run_id_field=20
- `lane_references`: task_lanes=12, run_lanes=24, task_lanes_without_claim=9, run_lanes_without_intake=0

## Findings

No structural identifier findings.

## Boundary

Legacy fields are classified, not rewritten. Backfill gaps remain advisory until an owner ruling promotes them to a hard gate.
