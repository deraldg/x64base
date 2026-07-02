# Diagram Metadata v2 Enrichment Worklist v1

Status: active worklist
Scope: ordered next-pass plan after the full structural v1-to-v2 restage candidate

## Purpose

This worklist turns the current diagram metadata v2 candidate state into a practical enrichment sequence.

It exists so the lane can move forward in a stable order:

1. structural carry-forward
2. proven enrichment
3. deferred enrichment only where keys are real

Structural carry-forward is already complete.

This document covers the next phase.

## Current status by enrichment lane

| Lane | Current state | Proven now | Deferred now | Recommended action |
|---|---|---|---|---|
| HELP artifact identity | boundary established | proof-sample `ABOUT -> DOT|ABOUT` crosswalk | full staged selfdoc/design rows do not expose HELP identities | keep full candidate blanks; enrich only real command/help rows |
| metadata command identity | sample-level proof exists | proof-sample `SYSCMD.CAN_NAME=ABOUT` | full staged selfdoc/design rows are not command entities | add command-facing rows later instead of overloading structural rows |
| metadata message identity | sample-level candidate only | `MSG_SYMBOL=COMMAND_STATUS` carried as candidate shape | no strong full-lane `SYSMSG` identity on current structural rows | defer until `SYSMSG` evidence is stronger |
| manual media/anchor identity | sample-level proof exists | `MEDIA_ID` and `ANCHOR_ID` from accepted manifests | full staged artifacts are mostly gates/pages/ledgers, not true media rows | enrich only true media artifacts or add separate media rows |

## Ordered workflow

### Step 1. Preserve the full structural candidate as-is

Keep these files conservative:

- [DIAGENTITY_IMPORT_v2.candidate.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGENTITY_IMPORT_v2.candidate.csv)
- [DIAGREL_IMPORT_v2.candidate.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGREL_IMPORT_v2.candidate.csv)
- [DIAGART_IMPORT_v2.candidate.csv](/D:/code/ccode/docs/diagrams/metadata/DIAGART_IMPORT_v2.candidate.csv)

Do not force:

- `CMDKEY`
- `CAN_NAME`
- `MSG_ID`
- `MSG_SYMBOL`
- `MEDIA_ID`
- `ANCHOR_ID`

into structural rows that are not truly those things.

### Step 2. Continue using proof-sample packets to validate joins

Use the proof-sample set for cross-family promotion tests:

- [DIAGRAM_METADATA_V2_PROOF_SAMPLE_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_PROOF_SAMPLE_v1.md)
- [DIAGRAM_METADATA_V2_COMMAND_ENRICHMENT_SAMPLE_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_COMMAND_ENRICHMENT_SAMPLE_v1.md)

This packet is the right place to prove:

- HELP-side command artifact joins
- compact `SYSCMD` command joins
- `SYSMSG` candidate joins
- `MANMEDIA` / `MANANCHOR` joins

before those shapes are spread into any larger staged import set.

### Step 3. Add new enriched rows instead of mutating old structural rows

When a future pass needs command/message/media identity, prefer adding new rows that are genuinely:

- `HELPARTIFACT`
- `COMMAND`
- `MESSAGE`
- `MEDIA`
- `ANCHOR`

instead of mutating older rows like:

- `METATABLE`
- `MANUALPAGE`
- `GATE`
- `SCHEMA`
- `LEDGER`

This keeps the lane normalized and honest.

### Step 4. Promote only after real feeder evidence is present

Each enrichment lane should promote only when the feeder has a usable physical identity:

- HELP: harvested `CMDKEY` or equivalent command/help artifact key
- command metadata: `CAN_NAME` and later `CMD_ID`
- message metadata: `SYMBOL` and later `MSG_ID`
- manual attachments: `MEDIA_ID` and `ANCHOR_ID`

If only prose/topic evidence exists, do not promote the identity field yet.

## Current lane boundaries

### HELP

See:

- [DIAGRAM_METADATA_V2_HELP_ENRICHMENT_BOUNDARY_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_HELP_ENRICHMENT_BOUNDARY_v1.md)

Current rule:

- full structural selfdoc/design rows stay blank for `CMDKEY`
- proof-sample command/help rows may carry `CMDKEY`

### Metadata command identity

Current rule:

- `ENAME -> SYSCMD.CAN_NAME` is valid only when the row is actually a canonical command entity
- selfdoc table rows like `SRCFILE` or `SRCUSAGE` are not command rows

### Metadata message identity

Current rule:

- message identity remains candidate-only until live `SYSMSG` evidence is strong enough
- HELP artifact names such as `COMMAND_STATUS` are useful crosswalk hints, not automatic runtime message truth

See:

- [DIAGRAM_METADATA_V2_MESSAGE_ENRICHMENT_BOUNDARY_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_MESSAGE_ENRICHMENT_BOUNDARY_v1.md)

### Manual media / anchor identity

Current rule:

- `RELATIVE_P` is a useful bridge
- final attachment truth should use `MEDIA_ID` and `ANCHOR_ID`
- gates, ledgers, and schema docs are not media rows

See:

- [DIAGRAM_METADATA_V2_MANUAL_ATTACHMENT_BOUNDARY_v1.md](/D:/code/ccode/docs/maintenance/lanes/metadata/DIAGRAM_METADATA_V2_MANUAL_ATTACHMENT_BOUNDARY_v1.md)

## Recommended next concrete passes

1. Maintain the HELP boundary and leave the full candidate set unchanged.
2. Create a separate command-facing enrichment packet when there are enough real command rows to justify it.
3. Create a separate message-facing enrichment packet only after `SYSMSG` is materially stronger.
4. Create a separate manual-media enrichment packet when diagram outputs are attached to true manual media records instead of staging docs.

The first command-facing enrichment packet now exists.

So the next command-side move is no longer packet design.

It is deciding how broad the command slice should become before it is promoted beyond sample scope.

## Practical bottom line

The lane is in a good state now.

We have:

- stable v2 headers
- proof-sample join shapes
- full structural restage candidates
- a documented HELP enrichment boundary

The right next move is selective enrichment by row kind, not blanket filling of empty identity columns.
