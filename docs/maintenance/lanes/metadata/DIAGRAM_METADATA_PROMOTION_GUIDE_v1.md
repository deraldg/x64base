# Diagram Metadata Promotion Guide v1

Status: active design/promotion guide
Scope: `DIAGRUN`, `DIAGENTITY`, `DIAGREL`, `DIAGART`, source-comment evidence, HELP artifacts, metadata catalog joins, manual/media attachment, Mermaid, and draw.io

## Purpose

This guide explains how the diagram metadata lane should promote upward into the existing DotTalk++ help, metadata, comments, and manual family without creating a second authority.

The main rule is simple:

- diagram facts should be normalized below the rendered document layer
- manuals should attach diagrams, not duplicate their authority
- HELP/manual/diagram outputs should consume approved metadata rather than compete with it

This guide is the practical join map for that promotion.

Companion join inventory:

- [DIAGRAM_METADATA_JOIN_COLUMN_INVENTORY_v1.md](D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_JOIN_COLUMN_INVENTORY_v1.md)

## Current state

Today the diagram lane is real as a staged/report-only design, not yet as a live runtime DBF family.

Current sources already present in the repo:

- [diagram_metadata_lane.md](/D:/code/ccode/docs/manuals/developer/04_selfdoc/diagram_metadata_lane.md:1)
- [DIAGENTITY_IMPORT_v1.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGENTITY_IMPORT_v1.csv:1)
- [DIAGREL_IMPORT_v1.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGREL_IMPORT_v1.csv:1)
- [DIAGART_IMPORT_v1.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGART_IMPORT_v1.csv:1)
- [generate_drawio_from_meta.py](/D:/code/ccode/tools/diagram/generate_drawio_from_meta.py:1)

Current boundary:

- staged CSVs and reports are allowed
- DBF proof exists only in isolated/report lanes
- live runtime `SYS*`, `SRC*`, HELP, and MAN* families remain the real surrounding authorities

## Promotion doctrine

The diagram lane should sit in this order:

```text
source comments and usage evidence
    -> comments/source metadata lane
    -> HELP and metadata catalog lanes
    -> diagram metadata normalization
    -> manual/media anchor attachment
    -> Mermaid / draw.io / publication outputs
```

The diagram lane is therefore not a replacement for:

- comments evidence
- `SYSCMD` / `SYSMSG`
- `HELP_ARTIFACTS`
- `MANANCHOR` / `MANMEDIA`

It is the classification and attachment layer between those systems and rendered diagrams.

## Proposed diagram tables

The staged v1 diagram family remains:

- `DIAGRUN`
- `DIAGENTITY`
- `DIAGREL`
- `DIAGART`

Their roles should be kept narrow.

### `DIAGRUN`

One row per diagram generation, validation, or promotion run.

Use it to track:

- run identity
- source lane
- review state
- generator/version
- promotion boundary

### `DIAGENTITY`

One row per diagram node or named entity.

Expected entity kinds include:

- metadata table
- help topic/artifact
- command
- subsystem
- workspace
- render artifact
- manual attachment target

### `DIAGREL`

One row per diagram edge or relation.

This is where evidence class must stay explicit:

- `SOLID` for runtime/report-proven joins
- `DASHED` for deferred but intended joins
- `DOTTED` for tentative/design-only joins

### `DIAGART`

One row per emitted artifact.

Expected artifact kinds include:

- Mermaid source
- draw.io source
- DOT/graph export
- CSV import seed
- render packet/report

## Existing authoritative feeders

The diagram lane should consume facts from the lanes that already own them.

### Comments/source evidence lane

Current authoritative source-comment structures include:

- `SRCFILE`
- `SRCBLOCK`
- `SRCLINE`
- `SRCUSAGE`
- `SRCCLASS`
- `SRCDISP`
- `SRCALIAS`
- `MEMO_LINES`

Runtime/workspace evidence:

- [comments.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/comments.dtschema:1)
- [new header schemas.txt](/D:/code/ccode/src/help/new header schemas.txt:43)

Current proven join spine:

- `SRCFILE -> SRCBLOCK ON FILEID`
- `SRCFILE -> SRCLINE ON FILEID`
- `SRCFILE -> SRCUSAGE ON FILEID`
- `SRCFILE -> SRCCLASS ON FILEID`
- `SRCUSAGE -> SRCCLASS ON COMMAND`

These are the best current feeders for ERD/data-flow and source-contract diagrams.

### HELP artifact lane

Current HELP artifact storage includes:

- `HELP_TOPIC`
- `HELP_SECTION`
- `HELP_LINE`
- `HELP_ARTIFACTS`

Workspace evidence:

- [help.dtschemas](/D:/code/ccode/dottalkpp/data/workspaces/help.dtschemas:1)

`HELP_ARTIFACTS` is the correct HELP-side bridge for diagram attachment and provenance when a HELP topic owns or references a generated artifact.

### Metadata catalog lane

Current metadata authority includes:

- `SYSCMD`
- `SYSSUBCMD`
- `SYSENTVAR`
- `SYSFUNC`
- `SYSHELP`
- `SYSMSG`
- `SYSARGS`
- `SYSFLDDIC`

Workspace evidence:

- [metadata.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/metadata.dtschema:1)
- [metadata_rel.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/metadata_rel.dtschema:1)

This is the right feeder for:

- command architecture diagrams
- routed/subcommand diagrams
- message family diagrams
- metadata/help alignment diagrams

### Manual attachment lane

Current accepted manual catalog includes:

- `MANANCHOR`
- `MANMEDIA`
- `MANSECTION`
- `MANPUB`
- `MANHASH`
- `MANREVIEW`
- `MANRUN`
- `MANAPPX`

Workspace evidence:

- [manual.dtschema](/D:/code/ccode/dottalkpp/data/workspaces/manual.dtschema:1)

Runtime/manual code evidence:

- [manual_catalog_reader.cpp](/D:/code/ccode/src/manual/manual_catalog_reader.cpp:1)
- [manual_catalog_resolver.cpp](/D:/code/ccode/src/manual/manual_catalog_resolver.cpp:1)

This is the correct top attachment layer for approved diagrams.

## Required join map

The following join map should govern future promotion work.

### Source evidence joins

Use `SRCFILE` and `SRCUSAGE` as the first promotion spine.

Recommended joins:

- `DIAGENTITY.source_file_id -> SRCFILE.FILEID`
- `DIAGENTITY.source_command -> SRCUSAGE.COMMAND`
- `DIAGREL.from_source_file_id -> SRCFILE.FILEID`
- `DIAGREL.to_source_file_id -> SRCFILE.FILEID`

If the diagram row represents a command contract rather than a file entity:

- join through logical command identity first
- do not bypass source evidence unless no source evidence exists

### Metadata joins

For command/system diagrams:

- `DIAGENTITY.command_name -> SYSCMD.CAN_NAME`
- `DIAGENTITY.subcommand_name -> SYSSUBCMD.SUBCMD`
- `DIAGENTITY.variant_owner -> SYSENTVAR.OWNER`
- `DIAGENTITY.message_symbol -> SYSMSG.SYMBOL` or equivalent seeded identity

Practical rule:

- the diagram lane should reuse metadata identities already accepted in `SYSCMD` and `SYSMSG`
- it should not invent a competing command or message naming system

### HELP joins

For HELP-surfaced diagrams:

- `DIAGART.help_owner -> HELP_ARTIFACTS`
- `DIAGENTITY.help_topic_slug -> HELP_TOPIC`
- `DIAGREL.help_context -> HELP_SECTION` or `HELP_LINE` only when truly needed

Practical rule:

- HELP owns help artifact attachment context
- diagram metadata owns diagram classification and relation evidence

### Manual joins

For approved diagrams that belong in the educational/manual layer:

- `DIAGART.manual_anchor -> MANANCHOR`
- `DIAGART.manual_media -> MANMEDIA`

This is the most important promotion rule in this guide:

- diagrams should be attached to manuals through `MANANCHOR` and `MANMEDIA`
- manuals should not absorb diagram structural truth into prose tables unless a prose summary is intentionally needed

## What should join to what

### `DIAGENTITY`

`DIAGENTITY` should marry primarily to:

- `SRCFILE`
- `SRCUSAGE`
- `SYSCMD`
- `SYSMSG`
- `HELP_TOPIC`
- `MANANCHOR`

It should represent the named thing shown in a diagram, not the emitted file.

### `DIAGREL`

`DIAGREL` should marry primarily to:

- `SRCFILE` / `SRCUSAGE` for evidence
- `SYSCMD` / `SYSSUBCMD` for command topology
- `HELP_ARTIFACTS` for HELP-facing artifact context

It should carry:

- edge style
- evidence class
- review state
- join note
- deferral reason if not solid

### `DIAGART`

`DIAGART` should marry primarily to:

- `HELP_ARTIFACTS`
- `MANMEDIA`
- `MANANCHOR`

It should represent the generated object:

- Mermaid file
- draw.io file
- PNG/SVG/PDF derivative
- staged CSV
- review report

### `DIAGRUN`

`DIAGRUN` should marry primarily to:

- diagram import/report sets
- generator version
- promotion review gates

It should not be overloaded with source-level semantics that belong in `SRC*`, `SYS*`, or HELP tables.

## Attachment model

The diagram lane should support both HELP and manual attachment, but at different levels.

### HELP-level attachment

Use when:

- a HELP topic needs an artifact reference
- a runtime help surface should point to a diagram or diagram packet

Best bridge:

- `HELP_ARTIFACTS`

### Manual/publication attachment

Use when:

- a developer manual section or educational packet should show a diagram
- a publication needs stable anchor/media binding

Best bridges:

- `MANANCHOR`
- `MANMEDIA`

### Policy

The policy should be:

- HELP references working artifacts
- manuals publish anchored artifacts
- diagram metadata tracks what the artifact means and why it is trusted

## Mermaid and draw.io consumers

Current draw.io generation already follows the right pattern:

- the seed owns architecture facts
- the generator owns parsing, validation, layout, and XML emission

Reference:

- [generate_drawio_from_meta.py](/D:/code/ccode/tools/diagram/generate_drawio_from_meta.py:1)

That pattern should remain.

Future rule:

- Mermaid and draw.io remain consumers
- `DIAGENTITY` / `DIAGREL` remain the normalized diagram fact layer
- manual/help layers remain attachment and publication layers

## Does this system fit the current help/manual family?

Yes. The family already fits this architecture well.

Why it fits:

- comments/source evidence already preserve structural facts
- metadata already classifies command/message surfaces
- HELP already has an artifact bridge
- manualgen already has anchor/media attachment tables
- draw.io generation already expects metadata-fed rendering rather than hand-coded architecture

Where it is still incomplete:

- diagram metadata is not yet promoted as a live DBF/runtime lane
- joins to `MANMEDIA` / `MANANCHOR` are doctrine-first, not yet runtime-proven as a maintained production path
- ERD/data-flow views still rely more on staged reports than on fully normalized live catalog rows

## What is ready now

The following diagram classes are ready or close to ready:

- command architecture diagrams from `SYSCMD`/`SYSSUBCMD`
- source-comment evidence diagrams from `SRCFILE`/`SRCUSAGE`
- help/manual pipeline diagrams
- metadata/help reconciliation diagrams
- artifact attachment diagrams for publication packets

## What should wait

The following should remain deferred until fuller promotion proof exists:

- automatic full runtime ERD generation from every DBF family
- aggressive mutation of manuals/help catalogs during diagram generation
- treating staged diagram CSVs as if they were already the live runtime authority

## Recommended next promotion gate

The next solid promotion gate should be:

1. keep `DIAG*` in report/staging doctrine
2. normalize join columns explicitly against `SRCFILE`, `SRCUSAGE`, `SYSCMD`, `HELP_ARTIFACTS`, `MANANCHOR`, and `MANMEDIA`
3. prove one full attachment path from staged diagram artifact to manual anchor/media target
4. prove one HELP artifact attachment path
5. only then authorize any live DBF/runtime lane promotion

## Practical bottom line

If you want diagrams to support manuals, HELP, Mermaid, and draw.io without redundancy, the correct model is:

1. source/comments and metadata own the facts
2. `DIAGENTITY` and `DIAGREL` normalize the diagram view of those facts
3. `DIAGART` tracks the emitted artifact
4. `HELP_ARTIFACTS` references working help artifacts
5. `MANANCHOR` and `MANMEDIA` attach approved diagrams into manuals/publications
6. Mermaid and draw.io render from the normalized layer rather than becoming the authority themselves

That is the cleanest way to make entity-relationship diagrams, data-flow diagrams, and architecture diagrams marry well with the current help family without making the manual redundant.
