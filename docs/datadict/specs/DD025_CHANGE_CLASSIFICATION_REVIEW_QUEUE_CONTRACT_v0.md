# DD-025 Change Classification / Review Queue Contract v0

Status: report-only design and tool skeleton.

DD-024 proved that the Data Dictionary redocumentation scanner can produce stable repeatable fingerprints. DD-023 can now report raw added/removed/changed file diffs. DD-025 is the next layer: it turns raw DD-023 file diffs into actionable review rows.

## Purpose

DD-025 classifies changes into review lanes:

- command / CLI source surface
- physical x64base engine surface
- workspace / relation / tuple surface
- MetaFact / metadata surface
- rules / xexpr surface
- build-profile / overlay boundary surface
- runtime and maintenance script surface
- manualgen/documentation surface
- Data Dictionary self-review surface

## Report-only boundary

DD-025 does not:

- scan the repo directly
- edit source
- build the program
- launch DotTalk++
- run HELP or CMDHELPCHK
- write DBF/CDX/LMDB/catalog data
- promote dictionary facts

It only reads DD-023 output and writes review-classification artifacts.

## Active tool

The repo drop-in installs:

```text
tools/datadict/review/change_classifier.py
```

## Expected local command

```powershell
& $py12 .	ools\datadicteview\change_classifier.py `
  --dd023 D:\code\ccode\docs\datadicteports\DDRUN-stable-A-to-B-diff-v0 `
  --out-dir D:\code\ccode\docs\datadicteview_queue\DD025-stable-A-to-B-v0 `
  --run-id DD025-stable-A-to-B-v0 `
  --profile ENGINE `
  --profile PROFESSIONAL
```

For the current stable zero-diff run, expected result is PASS with zero review rows. For any future source change, expected result is REVIEW or BLOCKED_REVIEW depending on severity.

## Outputs

- `dd025_change_classification_manifest.json`
- `dd025_classified_review_queue.csv`
- `dd025_classification_summary.csv`
- `dd025_severity_summary.csv`
- `dd025_review_lane_summary.csv`

## Design rule

A change is not just “changed.” It must be routed to a lane, given a severity, assigned gates, and blocked from promotion until reviewed.
