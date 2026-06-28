# DotTalk++ Manual Prose Guide v1

Status: working prose contract  
Audience: human developer, AI development agent, documentation maintainer  
Source root: `D:\code\ccode`  
Created: 2026-06-28

This guide explains how anchored evidence becomes readable manual prose.

The anchor map answers:

```text
What can we safely say?
```

The prose guide answers:

```text
How should we say it to a reader?
```

## Core Rule

Every manual section should have both:

1. An evidence anchor.
2. A prose role.

The anchor prevents unsupported claims. The prose role prevents the manual from becoming a dump of DBF rows, source symbols, and status files.

## Prose Roles

Use these roles when generating or editing manual text:

| Role | Purpose | Typical source | Reader shape |
|---|---|---|---|
| `orientation` | Explain what a subsystem is and why it matters. | Anchors, architecture notes, source boundaries. | Short paragraphs with a few named parts. |
| `tutorial` | Teach a reader to complete a workflow. | Runtime proof transcripts. | Steps, commands, expected readback, caveats. |
| `reference` | Catalog commands, functions, fields, files, or statuses. | HELP DBFs, META facts, data dictionary rows. | Stable entries, tables, syntax blocks. |
| `concept` | Explain a design idea such as x64 vectors or trinity headers. | Source contracts and design evidence. | Narrative plus a small example. |
| `caveat` | State a limit, drift, failure mode, or unproven edge. | Failed transcripts, drift reports, cmdhelpchk. | Direct warning with recovery or next proof. |
| `handoff` | Tell a developer or AI how to continue safely. | SelfDoc, manualgen, maintenance lanes. | Checklist, gates, next closure action. |
| `data_dictionary` | Describe objects, fields, relations, indexes, and evidence. | Data dictionary reports and schemas. | Object/field/relation entries, not tutorial prose. |

## Promotion Pattern

A good generated manual paragraph follows this pattern:

```text
Anchor -> reader purpose -> command or concept -> proof/readback -> caveat or next step
```

Example:

```text
CREATE X64 creates an x64 DBF table using the extended runtime path. Use it when you want a direct shell-created table rather than a schema-generated one. A safe proof sequence creates the table, runs STRUCT, runs FIELDS, inserts at least one row, and runs LIST or STATUS to confirm readback. Long logical names and metadata-vector behavior still need separate vector-name proof before they should be promoted as ordinary reader instructions.
```

That paragraph is useful because it does not merely name the command. It tells the reader when to use it, what proves it, and what remains bounded.

## Command and Function Prose

The command/function reference should not be prose-free, but it should not become a story either.

Each promoted command entry should contain:

```text
Name
Kind
Purpose
Syntax
Arguments
Example
Expected readback
Proof status
Related commands
Caveats
Anchor IDs
```

Command prose template:

```text
<COMMAND> <does what> for <reader purpose>. Use it when <context>. The basic form is <syntax>. A proofable example is <example>. Confirm success with <readback command/output>. Caveat: <limit, drift, or proof gap>.
```

Function prose template:

```text
<FUNCTION>() returns <value> for <expression context>. It is used in <WHERE/REPLACE/REPORT/etc.>. Arguments are <argument summary>. Proof status: <promoted/documented/deferred>. Caveat: <type, null, date, numeric, or compatibility boundary>.
```

## Tutorial Prose

Tutorial prose should be built from successful transcripts.

A tutorial section should include:

- what the reader is trying to accomplish
- setup assumptions
- commands in order
- expected readback
- common failure and recovery
- transcript path when relevant

Tutorial prose should not hide failed proof history. If an older transcript failed and a newer one succeeded, the tutorial should promote the newer path and place the older behavior in caveats or proof artifacts.

## Reference Prose

Reference prose should be generated from catalog rows and then lightly edited for human reading.

Reference entries should avoid vague verbs. Use direct verbs:

- creates
- opens
- attaches
- selects
- lists
- imports
- exports
- validates
- reports

Do not use reference prose to speculate about future behavior. Future work belongs in caveats, planning, or handoff sections.

## Concept Prose

Concept prose is the right place for:

- the trinity headers
- xBase lineage
- x64base theoretical limits
- vectored table and field names
- CNX/CDX/SET ORDER relationships
- x64 memo direction

Concept prose must mark the difference between:

- runtime-proven behavior
- source-supported design
- theoretical capacity
- compatibility background
- planned harvest work

## Caveat Prose

Caveats are not failures of the manual. They are how the manual stays honest.

Use caveat prose when:

- a transcript proves a failure mode
- manualgen reports drift
- HELP and META do not align
- a command exists but has not been proven recently
- source supports a feature but runtime behavior is not closed
- the user-mentioned concept has been captured before systematic harvest has finished

Good caveat prose is short and concrete:

```text
`DO X64` is preserved as legacy/profile vocabulary. The current reader quickstart uses `CREATE X64` directly because the proof transcript showed `DO X64` resolving as a missing script when no `X64.dts` profile exists.
```

## Data Dictionary Prose

Data dictionary prose should be more formal than tutorial prose.

It should describe:

- entity name
- field name
- field type and width
- source file or catalog row
- relation
- index/tag/order
- evidence anchor
- proof state

It should not teach a workflow unless the workflow is specifically about using the dictionary.

## AI Writing Rules

For future AI agents:

1. Read the anchor map before expanding a manual section.
2. Identify the prose role before writing.
3. Preserve the distinction between proven, observed, candidate, drift, and deferred.
4. Prefer one clear example over a large list of unproven possibilities.
5. Use HELP/META/catalog rows for names and syntax, but use transcripts for behavior.
6. Do not turn maintenance internals into reader commands.
7. Put developer-only mechanics in handoff or appendix prose.
8. Put unresolved work in caveats or next closure actions.

## Human Review Rules

Human review should ask:

- Does this paragraph tell the reader why they care?
- Is each command or claim anchored?
- Is behavior separated from theory?
- Is source-supported material labeled as source-supported?
- Is drift visible where it matters?
- Would a new developer know what proof to run next?

## Maturity Language

Use maturity language from `DOTTALKPP_MANUAL_MATURITY_MODEL_V1.md`.

When material is not fully proven, say so in a way that helps the reader:

```text
This command is source-supported and appears in HELP, but the reader manual still needs a current runtime transcript before this becomes a promoted tutorial.
```

When material is proven, state the proof path:

```text
This workflow is promoted because the transcript at <path> proves creation, mutation, and readback.
```

Avoid vague phrases such as "should work" or "probably supports." Use one of:

- captured
- anchored
- source-supported
- runtime-proven
- reader-ready
- reference-complete
- release-reviewed

## Next Prose Task

The next concrete prose task is to generate the first command/function reference batch for:

```text
CREATE X64
DDL CREATE DBF
USE
STRUCT
FIELDS
LIST
APPEND
REPLACE
RECNO
LOCK
UNLOCK
TABLE BUFFER
COMMIT
ROLLBACK
IMPORT
EXPORT
BROWSE
SET INDEX
SET ORDER
DOTSCRIPT
HELP
```

Each entry should use the command prose template and cite anchor IDs from `DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md`.
