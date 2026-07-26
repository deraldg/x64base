# DD-007 Physical Dictionary Extractor Skeleton v0

## Status

DD-007 creates the first report-only Python extractor skeleton for the DotTalk++ / x64base physical data dictionary.

It targets **Python 3.12+** and uses only the standard library. It is designed to run outside DotTalk++ and **does not launch the runtime, build C++, or mutate repository files**.

## What was produced

- `tools/dd007_physical_dictionary_extractor.py`
- `physical_dictionary_manifest_v0.schema.json` copied from DD-006
- `sample_run/physical_dictionary_manifest_v0.json`
- CSV projections for sources, tables, fields, indexes, schemas, runtime proof, warnings, and summary
- module map, trust-gate execution model, next-action table, and AUTOLOG

## Sample run counts

| Object | Count |
|---|---:|
| sources | 981 |
| tables | 1 |
| fields | 9 |
| indexes | 2 |
| schemas | 3 |
| runtime_proof | 24 |
| warnings | 1 |

## Current evidence harvested

The sample run scanned the corrected repo package read-only. Because the repo package contains source/schema/config material but no runtime DBF directory, DD-007 produced source/declaration evidence rather than runtime-open proof.

Observed declared table evidence comes from `src/schemas/students.schema.json`. This remains a declared/sample schema fact and must not be promoted as engine/core proof without profile review.

## Why this matters

DD-005 identified where physical dictionary facts should come from. DD-006 defined the manifest shape. DD-007 now gives the project an executable, report-only bridge:

```text
repo/source/schema/dbf evidence
  -> DD-006 manifest JSON
  -> CSV projections
  -> later x64base staging/import plan
```

The extractor is intentionally conservative. It preserves the distinction between:

- source anchor present
- declared schema fact
- physical DBF header parsed
- runtime-open proof
- promotion-ready catalog row

## Boundaries preserved

No repo mutation occurred. No source edits occurred. No CMake edits occurred. No C++ build occurred. DotTalk++ was not launched. No HELP, META, CMDHELPCHK, DBF, CDX, LMDB, runtime catalog, or production SelfDoc metadata mutation occurred.
