# DD-018 Evidence Reconciliation and Projection Skeleton v0

Date: 2026-05-27  
Repo package examined: `ccode_homegrown_20260527-055727.zip`  
Repo package SHA-256: `6e19963fa1d975128bc14b39a3d4ca1262743f3c2563759873f6b63ea33f36b4`  
Mode: report-only skeleton / no runtime launch / no catalog mutation

## Status

DD-018 creates the first reconciliation layer between dictionary evidence streams:

```text
DD-007 source/schema manifest
DD-017 static DBF header projection
future DD-014/DD-016 runtime transcript proof
  -> DD-018 evidence stack
  -> candidate projections
  -> conflict queue
  -> later reviewed catalog promotion
```

This package is still report-only. It does not build C++, does not run DotTalk++, does not open project DBFs, and does not mutate HELP, META, CMDHELPCHK, DBF, CDX, LMDB, or catalog tables.

## Why DD-018 matters

The data dictionary must not collapse different truth levels into one confident-looking row. DD-018 keeps the evidence stack visible:

```text
runtime proof
static byte parse
declared schema
source contract / registry
generated report
AI draft / design proposal
```

The reconciler selects a candidate projection, but it also emits a conflict queue. A candidate projection is not a promoted dictionary fact.

## Included tool

```text
tools/dd018_evidence_reconciler.py
```

The skeleton accepts repeated JSON inputs:

```text
python tools/dd018_evidence_reconciler.py   --input sample_inputs/dd007_sample_physical_manifest_v0.json   --input sample_inputs/dd017_sample_static_projection_v0.json   --outdir sample_output
```

## Sample run counts

```text
input files:          2
table evidence rows:  3
field evidence rows:  14
projected objects:    17
conflict rows:        0
```

The sample combines DD-007 declared/source evidence with DD-017 synthetic static DBF parser fixtures. The DD-017 fixture rows are not project runtime data and not runtime proof.

## Catalog projections

DD-018 reserves these projection surfaces:

```text
DD_TABLE_CANDIDATE
DD_FIELD_CANDIDATE
DD_EVIDENCE_STACK
DD_CONFLICT_QUEUE
DD_MANIFEST_INPUT_INDEX
```

Promotion targets remain later, reviewed objects such as:

```text
DD_TABLE
DD_FIELD
DD_FIELD_PHYSICAL
DD_TABLE_VERIFY
DD_SOURCE
DD_RUNTIME_PROOF
DD_REVIEW_QUEUE
```

## Trust rule

Runtime physical facts should outrank declared or inferred facts, but not silently overwrite them. DD-018 preserves lower-ranked evidence as provenance or conflict context.

## Boundary preserved

No repo files changed. No source edits, no build, no runtime launch, no DBF/CDX/LMDB/memo open, no HELP/META/CMDHELPCHK mutation, and no catalog promotion occurred.
