# DD-029 Generated Package / Maintenance Artifact Disposition Policy v0

## Purpose

DD-029 handles the first real blocked DD-028 result after the accepted Data Dictionary baseline. The blocked result was not caused by product-source drift. It was caused by expected Data Dictionary tool additions plus root-level MDO-266 package folders and savepoint/report evidence.

DD-029 introduces a report-only disposition layer that separates:

- product/source drift
- Data Dictionary self-changes
- Data Dictionary tooling changes
- generated or temporary maintenance package artifacts
- manualgen evidence artifacts
- savepoint/runlog evidence
- runtime data/backend changes

The goal is not to hide change. The goal is to classify it so future baseline acceptance can be deliberate and evidence-based.

## Why this package exists

DD-028 correctly reported:

- added: 88
- changed: 1
- review_rows: 89
- high: 12
- status: BLOCKED_REVIEW

DD-026 triage showed the high rows were root-level `mdo_266_*` PowerShell scripts requiring script-boundary review, while most other rows were Data Dictionary lane additions. That is exactly the kind of distinction the redocumentation system should make before accepting a new baseline.

## Active tool

```text
tools/datadict/disposition/artifact_disposition.py
```

## Policy file

```text
docs/datadict/policies/generated_artifact_policy_v0.json
```

## Inputs

A DD-025 classification run, DD-028 run packet, or review queue CSV.

Common local input:

```text
docs/datadict/reports/DD028-check-current-v0
```

## Outputs

```text
dd029_artifact_disposition_manifest.json
dd029_artifact_disposition_rows.csv
dd029_disposition_summary.csv
dd029_lane_summary.csv
dd029_required_action_summary.csv
dd029_policy_effective.json
DD029_ARTIFACT_DISPOSITION_REPORT.md
```

## Key dispositions

```text
DATADICT_LANE_CHANGE
DATADICT_TOOLING_CHANGE
MAINTENANCE_PACKAGE_SCRIPT
MAINTENANCE_PACKAGE_EVIDENCE
MANUALGEN_REPORT_EVIDENCE
RUNLOG_OR_SAVEPOINT_EVIDENCE
PRODUCT_SOURCE_CHANGE
RUNTIME_SCRIPT_CHANGE
RUNTIME_DATA_OR_BACKEND_CHANGE
HUMAN_TRIAGE_REQUIRED
```

## Boundary

DD-029 is report-only. It does not edit source, run builds, launch DotTalk++, mutate HELP/META/CMDHELPCHK, write DBF/CDX/LMDB/catalog data, or promote dictionary facts.
