# DEV-08 DBF x32 / x64 Formats

```yaml
page_id: DEV-08
title: DBF x32 / x64 Formats
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Current x64 evidence

Strong runtime/file evidence from inspected `TEACHERS.DBF`:

```text
first byte: 0x64
record count: 20
header length: 321
record length: 95
field descriptors begin at offset 0x60 / 96
first record at offset 321
EOF byte 0x1A at offset 2221
```

## Future/maturing META feeders

- `SYSFLDDIC`: field dictionary and logical names/roles/value kinds
- `SYSCMD`: STRUCT/FIELDS/CREATE command identity
- `SYSARGS`: command argument metadata for schema/field commands
- `SYSHELP`: schema/field concept help

## Crosswalk target

`dbf-schema-crosswalk-v0.csv`

## Canaries

- x64 format evidence needs source cross-check before final spec.
- field-name length/mangling policy needs current source verification.
- memo fields require MemoManager-aware documentation.
- SYSFLDDIC row contents not yet crosswalked.
- Canonical structural boundary proof now lives in:
  - `dottalkpp/data/scripts/canaries/x64_matrix_metrics_boundary_canary.dts`
- That canary intentionally creates two disposable x64 tables:
  - one above the old signed 16-bit record-length barrier
  - one above the old 16-bit compatible mirror ceiling
- Current CREATE parser still caps one X64 character field at `4096`, so the
  canary crosses the widened record-metrics boundaries with multiple wide `C`
  fields rather than a single oversized field.
