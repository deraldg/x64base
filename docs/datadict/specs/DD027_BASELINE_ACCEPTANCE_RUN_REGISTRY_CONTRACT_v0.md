# DD-027 Baseline Acceptance / Run Registry Contract v0

## Purpose

DD-027 accepts a green Data Dictionary redocumentation run as the comparison baseline for future changes.

It is deliberately **report-only**. It does not create DBFs, promote dictionary facts, mutate HELP/META/CMDHELPCHK, rebuild manuals, launch DotTalk++, or edit source.

## Inputs

- DD-022/DD-024 scan manifest: `dd022_redoc_run_manifest.json`
- Optional but strongly expected DD-023 clean diff manifest: `dd023_redoc_diff_manifest.json`
- Optional but strongly expected DD-026 clean triage manifest: `dd026_triage_manifest.json`

## Outputs

- `dd027_baseline_acceptance_manifest.json`
- `dd027_run_registry_row.csv`
- `dd027_gate_ledger.csv`
- `dd027_boundary_ledger.csv`
- `dd027_artifact_manifest.csv`
- `dd027_next_comparison_target.json`
- `DD027_BASELINE_ACCEPTANCE_REPORT.md`

## Acceptance rule

A baseline is accepted only when:

1. scan status is `PASS`
2. source file count is greater than zero
3. scan warnings are zero unless explicitly allowed
4. aggregate fingerprint is present
5. clean diff proof is supplied and reports `PASS`, with zero added/removed/changed files
6. clean triage proof is supplied and reports `PASS`, with zero review rows and zero high-severity rows
7. no-mutation boundary ledger is green

## Boundary

DD-027 writes only its output packet under `docs/datadict/baselines/<baseline_id>/` or another explicitly provided output directory.

It does not authorize catalog promotion. A later DD package must explicitly authorize any staging import, x64base DBF creation, or HELP/META/CMDHELPCHK integration.


## v1.1 compatibility patch

Baseline acceptance now reads DD-024 nested `exclusion_policy.stable_source_count`, `exclusion_policy.excluded_count`, and `exclusion_policy.aggregate_fingerprint` fields from DD-024-compatible `dd022_redoc_run_manifest.json` files. This is a report-only parser compatibility repair; no promotion or protected-system mutation is authorized.
