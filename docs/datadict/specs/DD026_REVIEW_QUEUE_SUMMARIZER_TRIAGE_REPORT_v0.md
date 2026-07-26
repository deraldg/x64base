# DD-026 Review Queue Summarizer / Triage Report v0

## Purpose

DD-026 turns DD-025 review queues into a compact triage packet. DD-025 can produce thousands of rows; DD-026 summarizes them by lane, severity, gate, root path, and recommended next action.

## Position in the redocumentation loop

```text
DD-022 scan
DD-024 stable exclusions/fingerprint
DD-023 diff
DD-025 classify changes
DD-026 summarize and triage review queue
```

## Active tool

```text
tools/datadict/review/triage_report.py
```

## Inputs

A DD-025 output directory or `dd025_change_classification_manifest.json`.

## Outputs

- `dd026_triage_manifest.json`
- `DD026_TRIAGE_REPORT.md`
- `dd026_lane_triage.csv`
- `dd026_severity_triage.csv`
- `dd026_gate_triage.csv`
- `dd026_top_roots.csv`
- `dd026_change_class_triage.csv`
- `dd026_promotion_disposition_triage.csv`
- `dd026_recommended_next_actions.csv`
- `dd026_sample_review_rows.csv`

## Boundary

Report-only. DD-026 does not edit source, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or promote dictionary facts.
