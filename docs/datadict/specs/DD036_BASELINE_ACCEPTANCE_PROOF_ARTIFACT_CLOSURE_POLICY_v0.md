# DD-036 Baseline Acceptance Proof Artifact Closure Policy v0

## Purpose

DD-036 handles the small artifact class that appears immediately after a new Data Dictionary baseline is accepted.

During the `DDBASE-stable-v2` sequence, the fresh A/B proof was clean and DD-027 accepted the baseline, but the final DD-034 check saw six new rows:

- three files under `docs/datadict/baselines/DDBASE-stable-v2/`
- three clean proof files under `docs/datadict/review_queue/DD025-stable-v2-A-to-B/` and `DD026-stable-v2-A-to-B/`

These are not product-source drift. They are baseline acceptance/proof artifacts created by the acceptance sequence after the stable-B scan.

## Scope

DD-036 classifies:

| Class | Meaning |
|---|---|
| `BASELINE_ACCEPTANCE_PACKET` | DD-027 baseline packet for the same baseline id |
| `BASELINE_STABLE_PROOF_PACKET` | DD-025/DD-026 clean A-to-B proof artifacts for the same stable baseline version |
| `NON_ACCEPTANCE_ARTIFACT` | anything else |

## Statuses

| Status | Meaning |
|---|---|
| `BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_REVIEW` | rows are acceptance/proof artifacts but explicit acceptance flag was not supplied |
| `BASELINE_ACCEPTANCE_ARTIFACT_CLOSURE_ACCEPTED` | all rows are accepted acceptance/proof artifacts |
| `BLOCKED_NON_ACCEPTANCE_ARTIFACT_REVIEW` | at least one row is not explained by the acceptance/proof policy |

## Boundary

Report-only. DD-036 does not accept or replace a baseline, edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or move/delete files.
