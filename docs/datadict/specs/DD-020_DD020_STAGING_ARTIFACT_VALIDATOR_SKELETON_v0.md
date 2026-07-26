# DD-020 Staging Artifact Validator Skeleton v0

Date: 2026-05-27  
Boundary: REPORT_ONLY  
Input validated: DD-019 catalog-staging import plan package  
Mutation status: none

## Purpose

DD-020 creates the first repeatable validator for Data Dictionary staging artifacts.

This is the next step in the redocumentation direction: after extraction, reconciliation, and staging projection, the staging artifacts need a reusable validator that can be run every time the codebase, scripts, schemas, HELP, rules, or runtime-proof evidence changes.

DD-020 validates staging packages. It does **not** import them.

## Current sample validation result

| Item | Count / status |
|---|---:|
| Overall sample status | REVIEW |
| Validation checks | 30 |
| PASS checks | 26 |
| REVIEW checks | 4 |
| FAIL checks | 0 |
| Files hashed | 23 |
| Table artifacts checked | 12 |
| Gate rows checked | 5 |
| Referential checks | 7 |

The sample status is expected to be `REVIEW`, not final green, because DD-019 intentionally planned more staging table families than it fully field-specified. That is useful: DD-020 is already catching the gap between catalog table planning and import-execution readiness.

## What DD-020 validates

- package directory exists;
- staging manifest JSON is parseable;
- catalog table plan and field plan exist;
- staging CSV artifacts exist where expected;
- required columns are present;
- required values are not silently blank without review;
- file hashes are captured for repeatability;
- object/evidence/attribute/edge references are checked lightly;
- manifest object/evidence/conflict counts match sample CSV rows;
- `PROMOTION_AUTHORIZED` remains blocked for report-only packages.

## Why this matters for redocumentation

A one-time dictionary pass would decay as soon as the source code changed. DD-020 establishes a validator that can be rerun as part of a regular cycle:

```text
rescan -> manifest -> reconcile -> stage -> validate -> review -> promote only if authorized
```

The validator output becomes its own evidence source for later runs. It can support change detection, drift reports, review queues, and guarded documentation regeneration.

## Sample REVIEW items

DD-020 found that DD-019 has planned staging table families whose field specifications are not yet complete in the DD-019 field-plan CSV. This is not a runtime defect; it is a readiness finding.

The affected planned families are expected to include:

```text
DD_WARNING
DD_PROFILE_SCOPE
DD_PROMOTION_QUEUE
DD_IMPORT_FILE
```

Those table families should either receive field definitions in the next staging-schema package or remain explicitly deferred.

## Files generated

```text
tools/dd020_staging_artifact_validator.py
sample_output/dd020_validation_report_v0.json
sample_output/dd020_validation_summary_v0.csv
sample_output/dd020_validation_checks_v0.csv
sample_output/dd020_file_manifest_v0.csv
sample_output/dd020_table_validation_v0.csv
sample_output/dd020_gate_validation_v0.csv
sample_output/dd020_referential_validation_v0.csv
dd020_validator_module_map_v0.csv
dd020_validation_contract_v0.csv
dd020_trust_gates_v0.csv
dd020_repo_placement_candidates_v0.csv
schemas/dd020_validation_report_v0.schema.json
```

## Boundary

DD-020 performs no repo mutation, no source edits, no build, no runtime launch, no DBF/CDX/LMDB/catalog mutation, no HELP/META/CMDHELPCHK mutation, and no catalog promotion.

## Result

DD-020 is green as a validator skeleton and sample run, with expected REVIEW findings against DD-019 staging-schema completeness.
