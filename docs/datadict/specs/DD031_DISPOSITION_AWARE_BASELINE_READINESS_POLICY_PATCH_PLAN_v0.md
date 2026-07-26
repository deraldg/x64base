# DD-031 Disposition-Aware Baseline Readiness / Policy Patch Plan v0

## Purpose

DD-031 combines DD-028 baseline comparison, DD-029 artifact disposition, and DD-030 script-boundary disposition to determine whether current repository changes are ready for a new Data Dictionary baseline review.

DD-031 does **not** accept a baseline. It only reports readiness and proposes policy changes needed before a new baseline such as `DDBASE-stable-v1` can be accepted.

## Inputs

- DD-028 run packet: current repo versus accepted baseline.
- DD-029 run packet: artifact disposition of the DD-028 review queue.
- DD-030 run packet: script-boundary disposition for maintenance package scripts.

## Outputs

- `dd031_baseline_readiness_manifest.json`
- `DD031_BASELINE_READINESS_REPORT.md`
- `dd031_readiness_gate_ledger.csv`
- `dd031_disposition_rollup.csv`
- `dd031_exclusion_policy_patch_proposal.json`
- `dd031_next_baseline_plan.csv`
- `dd031_boundary_ledger.csv`

## Status meanings

- `READY_FOR_BASELINE_REVIEW`: the current changes are explained by disposition gates, but a new baseline has not been accepted.
- `BASELINE_UNCHANGED`: no meaningful changes were present.
- `BLOCKED_BASELINE_READINESS`: unresolved gates remain.

## Boundary

DD-031 is report-only. It does not edit source, move/delete files, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or accept/replace a baseline.
