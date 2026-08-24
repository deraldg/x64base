# DEV-08 DBF x32 / x64 Formats

```yaml
page_id: DEV-08
title: DBF x32 / x64 Formats
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-07-07
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being
treated as a replacement for META. They are the current available evidence
until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META
feeder tables.

## Current x64 geometry status

The x64 lane has been reopened structurally beyond the old 16-bit-era metrics
barriers.

Important distinction:

- classic headers still carry compatibility mirrors such as record length and
  data-start values
- x64 runtime truth is not limited to those old mirrors when the wide x64
  extension values are present

This means:

- old mirror fields still matter for compatibility and inspection
- they are no longer the whole x64 story
- runtime and canary proof must be read with the wide x64 extension in mind,
  not only the legacy header mirror

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

## Practical interpretation

The canary does not prove that every older tool, export path, or mirror-only
reader can consume those wider tables unchanged.

It proves a narrower but important claim:

- x64 open/create/runtime geometry is no longer confined to the historical
  signed 16-bit record-length barrier
- the classic mirror layer and the current creation/parser layer remain
  separate concerns

That is the correct teaching point for this chapter:

- file-format ambition
- runtime-open/runtime-mutation capacity
- parser/create convenience limits

are related, but not identical layers.

## Current creation-path constraint

Current practical construction still includes a parser-side cap of `4096` for a
single `CREATE X64` character field.

So the current recommended proof strategy is:

- use multiple wide `C(4096)` fields when crossing widened record-metrics
  boundaries
- treat single-field oversize ambitions as a later parser-path enhancement, not
  as a refutation of the current x64 geometry work
