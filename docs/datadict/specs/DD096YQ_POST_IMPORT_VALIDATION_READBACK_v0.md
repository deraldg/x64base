# DD096YQ Post-Import Validation / Readback v0

Created UTC: `2026-05-29T02:52:03+00:00`

## Purpose

DD096YQ validates the DD096Y staged import into the DD096X parallel x64 Data Dictionary proof schema.

It writes expected-count ledgers and a DotTalk++ validation DTS.

Expected record counts after DD096X + DD096Y:

```text
DATA_DICTIONARY_OBJECTS             10
DATA_DICTIONARY_OBJECT_ATTRIBUTES  127
DATA_DICTIONARY_RELATION_EDGES      16
DATA_DICTIONARY_EVIDENCE_RECORDS     7
DATA_DICTIONARY_GATE_RECORDS         3
DATA_DICTIONARY_RUNS                 2
```

## Boundary

Post-import validation only. No active Data Dictionary catalog replacement.
