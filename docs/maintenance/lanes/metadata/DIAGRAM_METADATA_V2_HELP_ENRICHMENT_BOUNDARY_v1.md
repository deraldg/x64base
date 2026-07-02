# Diagram Metadata v2 HELP Enrichment Boundary v1

Status: active boundary note
Scope: when `CMDKEY` may be promoted into diagram metadata v2 rows

## Purpose

This note records the current hard boundary for HELP enrichment in the diagram metadata lane.

The rule is simple:

- fill `CMDKEY` only when the staged diagram row already corresponds to a real harvested HELP-side command artifact
- leave `CMDKEY` blank when the staged diagram row is only a selfdoc table, a design table, a draft page, a gate, or a staging artifact

This keeps the v2 candidate files evidence-governed.

## Current harvested HELP proof

The harvested HELP artifact lane proves that real command-facing rows exist with concrete identities such as:

- `COMMAND=ABOUT`
- `CMDKEY=DOT|ABOUT`
- `OWNER=COMMAND:ABOUT`
- `NAME=COMMAND_STATUS`

Source:

- [HELP_HELP_ARTIFACTS.csv](/D:/code/ccode/docs/manuals/developer/manualgen/harvested/HELP_HELP_ARTIFACTS.csv)

This is sufficient to support the proof-sample HELP crosswalk for command-facing rows like `ABOUT`.

## Current full staged-lane boundary

The full structural v2 candidate set does not yet consist of command-facing HELP artifacts.

It mainly contains:

- selfdoc metadata tables such as `SRCFILE`, `SRCBLOCK`, `SRCLINE`, `SRCUSAGE`, `SRCCLASS`
- the `MEMO_LINES` staging table
- staged design tables such as `DIAGRUN`, `DIAGENTITY`, `DIAGREL`, `DIAGART`
- draft/manual pages
- gates
- staging manifests
- schema notes
- promotion ledgers

These rows are documented and useful, but they do not themselves expose harvested HELP artifact identity.

Result:

- `CMDKEY` remains blank in the full v2 candidate files by design

## Proven exception

The proof-sample packet is allowed to carry `CMDKEY` because it uses a true harvested HELP artifact row.

That is a different case from the full staged selfdoc/design set.

See:

- [DIAGRAM_METADATA_V2_PROOF_SAMPLE_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_PROOF_SAMPLE_v1.md)

## Promotion rule

Use this rule during future enrichment:

1. If the diagram row is a real command/help artifact row with harvested identity, fill `CMDKEY`.
2. If the diagram row is only a table, draft, gate, manifest, schema note, or design record, leave `CMDKEY` blank.
3. If a later crosswalk introduces a separate command-facing entity row, that new row may carry `CMDKEY` even if the older structural row remains blank.

## Practical bottom line

Current status is:

- HELP enrichment by proof sample: yes
- HELP enrichment across the full staged selfdoc/design restage set: not yet

That is the correct result with the current evidence.
