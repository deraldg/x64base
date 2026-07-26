# DD027_AUTOLOG_v0

Date: 2026-05-27
Subsystem: Data Dictionary / redocumentation / baseline acceptance
Files generated: DD-027 package and repo drop-in
Intent: Accept a green stable Data Dictionary scan/diff/triage sequence as the next comparison baseline.
Behavior preserved: report-only boundary; no source edits; no build; no runtime launch; no HELP/META/CMDHELPCHK mutation; no DBF/CDX/LMDB/catalog mutation; no dictionary promotion.
Sample result: ACCEPTED_BASELINE with gate_failures=0 and boundary_failures=0.
Risk: A real baseline should only be accepted after the user confirms the selected scan/diff/triage run IDs are the intended baseline.
Next recommended action: install DD-027 and accept `DDRUN-stable-B-v0` using the clean `DDRUN-stable-A-to-B-diff-v0` and `DD026-stable-A-to-B-v0` proofs.


## v1.1 compatibility patch

Baseline acceptance now reads DD-024 nested `exclusion_policy.stable_source_count`, `exclusion_policy.excluded_count`, and `exclusion_policy.aggregate_fingerprint` fields from DD-024-compatible `dd022_redoc_run_manifest.json` files. This is a report-only parser compatibility repair; no promotion or protected-system mutation is authorized.
