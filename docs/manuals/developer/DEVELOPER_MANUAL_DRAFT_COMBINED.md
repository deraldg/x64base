# DotTalk++ / x64base Developer Manual Draft Bundle

Generated base: 2026-05-24
Manual patch refresh: 2026-07-07

> Draft drop-in bundle. Harvested HELP/META CSVs and generated crosswalks are pending.
> This file is a working draft bundle. It is not the promoted primary reader artifact unless the reader pointer is explicitly updated.


---

# DEV-00 Evidence Rules

```yaml
page_id: DEV-00
title: Evidence Rules
status: DRAFT_PATCHED
last_verified: 2026-07-07
evidence_classes: [HELP, METADATA, SOURCE, PROVEN, CANARY, PLANNED]
```

## Purpose

The Developer Manual is a controlled publication layer over SelfDoc evidence, source verification, runtime proof, and manual review.

## Governing doctrine

```text
HELP explains broadly.
META organizes semantically.
CMDHELPCHK validates reflected structure.
Source verifies ownership.
Runtime proves behavior.
SelfDoc preserves provenance.
The Master Document Organizer assembles the manuals.
The website is an attached publication lane, not an authority by default.
```

## Practical pipeline

```text
HELP/META/CMDHELPCHK evidence first
source verification second
runtime proof final for behavior
manual prose last
website prose is harvested only where it is explicitly outside the documented inventory
```

## Evidence precedence

1. Runtime proof for exact behavior.
2. HELP `USAGE_CONTRACT` rows, `CONFID=AUTHORITATIVE`.
3. HELP `CURATED_DOC` rows, `CONFID=CURATED`.
4. HELP `REGISTRY` rows, `CONFID=REFLECTED`, for status only.
5. CMDHELPCHK reflection reports.
6. META active semantic seed rows.
7. Source implementation/prototype inventory.
8. SOURCE_MINER inferred rows, review required.
9. Historical documents.
10. Website prose and presentation copy, unless explicitly elevated by review.

Important nuance: META is not lower quality than HELP; it is currently narrower in the observed seed.

## Manual and website source policy

The manual and the website should draw from the same project evidence spine:

- source/runtime contracts
- HELP
- metadata
- CMDHELPCHK
- SelfDoc provenance
- reviewed canaries

The manual does not treat the website as an authority just because the website
happens to be newer or more polished.

Working rule:

- if a fact belongs to documented runtime/source inventory, harvest it from the
  project lanes directly
- if a website section is presentation-only and explicitly outside the
  documented inventory, that prose may be harvested into the manual after review
- do not copy implementation facts from the website back into the manual when
  the project lanes already own those facts

## Review statuses

`ACCEPT`, `PUBLIC_READY`, `DEVELOPER_ONLY`, `INTERNAL`, `SCAFFOLD`, `REVIEW`, `CONFLICT`, `GAP`, `CANARY`, `BLOCKED`, `HISTORICAL`, `SUPERSEDED`.

## Standing canary rules

- HELP breadth is not behavior proof.
- META absence is not project absence.
- SOURCE_MINER inference is not public documentation.
- Runtime proof is path-specific.
- Canaries remain visible until closed with evidence.


## Working rule

```text
Read HELP broadly.
Read META semantically.
Validate with CMDHELPCHK.
Verify with source.
Prove with runtime.
Assemble with manuals.
Publish to website as an attached view.
```

---

# DEV-01 Project Identity

```yaml
page_id: DEV-01
title: Project Identity
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Identity

DotTalk++ / x64base is a working educational xBase / FoxPro-inspired database runtime, command shell, teaching system, metadata experiment, and architecture lab built in modern C++.

It is also now a SelfDoc system: a runtime/documentation/metadata environment that mines HELP and metadata evidence, validates reflected command/function structure, and uses that evidence to assemble manuals.

## Short form

```text
DotTalk++ is a visible database runtime with an evidence-backed documentation and metadata spine.
```

## What it is

- an educational database runtime
- an xBase/FoxPro-inspired command environment
- a modern C++ architecture lab
- a visible database teaching system
- a metadata and HELP evidence system
- a SelfDoc/manual-generation platform

## What it is not

- a finished commercial DBMS
- a blind FoxPro clone
- a nostalgia-only museum project
- a single-purpose DBF utility
- a documentation project separate from runtime

## SelfDoc identity

Observed HELP evidence:
- HELP.COMMANDS: 402 records
- HELP.HELP_TOPIC: 471 records
- HELP.HELP_ARTIFACTS: 5412 records

Observed META evidence:
- META.SYSCMD: 40 records
- META.SYSSUBCMD: 12 records
- META.SYSENTVAR: 12 records
- META.SYSFUNC: 0 records in the observed seed
- META.SYSHELP: 8 records

Observed runtime messaging/locale evidence:
- command surface: `src/cli/cmd_msgmgr.cpp`
- operator shell surface: `src/cli/cmd_set.cpp`
- message provider: `src/help/message_catalog.cpp`
- locale provider: `src/help/locale_spine_catalog.cpp`
- active message tables:
  - `dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf`
  - `dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf`
- active locale tables:
  - `dottalkpp/data/locale/SYSTEM_LOCALES.dbf`
  - `dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf`

Important correction:

- `SYSMSG` is still the compact metadata feeder and planning surface
- `SYSTEM_MESSAGES` / `SYSTEM_MESSAGE_TEXT` are active runtime catalog tables
- locale work is no longer only a future publication concern because a shared
  runtime locale spine already exists structurally
- users do not reach this lane only through `MSGMGR`; the normal shell entry
  surface also runs through `SET LANGUAGE`, `SET LOCALE`, `SET MESSAGE CATALOG`,
  `SET MESSAGE PROOF`, and `SET MESSAGE EMIT`

These counts are identity evidence: HELP is broad and richly mined; META is semantic and seeded but currently narrower.

---

# DEV-02 Build and Runtime Layout

```yaml
page_id: DEV-02
title: Build and Runtime Layout
status: DRAFT
last_verified: 2026-07-08
```

## Three estates

```text
source estate
  implementation and build ownership

runtime estate
  scripts, data, workspaces, HELP/META stores, smoke fixtures

manual/evidence estate
  inventories, crosswalks, proof ledgers, diagrams, manuals
```

## Source estate

Primary C++ source roots:

```text
D:\code\ccode\src
D:\code\ccode\include
D:\code\ccode\bindings
```

## Runtime estate

Primary runtime/data/script estate:

```text
D:\code\ccode\dottalkpp
```

## HELP setup

```text
do cmdhelp
  DBF     = d:\code\ccode\dottalkpp\data\HELP
  INDEXES = d:\code\ccode\dottalkpp\data\INDEXES\HELP
```

## META setup

```text
do metadata
  DBF     = d:\code\ccode\dottalkpp\data\dbf\metadata
  INDEXES = d:\code\ccode\dottalkpp\data\indexes\metadata
  LMDB    = d:\code\ccode\dottalkpp\data\lmdb\metadata
```

Observed correction: `do meta` fails; `do metadata` works.

## Practical rule

Source verifies where behavior lives. Runtime shows what happens. HELP and META store mined evidence. The manual assembles the verified truth.

---

# DEV-03 Source Tree Map

```yaml
page_id: DEV-03
title: Source Tree Map
status: DRAFT_PATCHED
last_verified: 2026-05-24
```

## Key correction

Source is a verification and provenance sidecar. It is not the primary manual-generation source now that HELP/META/CMDHELPCHK mined evidence exists.

## Source estate boundary

```text
D:\code\ccode\src
D:\code\ccode\include
D:\code\ccode\bindings
```

Runtime/data/script estate:

```text
D:\code\ccode\dottalkpp
```

## Major source lanes

| Lane | Primary area | Manual role |
|---|---|---|
| CLI | `src/cli` | command handlers, dispatch, DotScript, HELP bridge |
| HELP / SelfDoc | `src/help`, HELP bridge code | source miner, HELP DATA, validators |
| xBase / DbArea | `src/xbase`, `include/xbase.hpp` | table engine |
| Indexing | `src/xindex`, `src/cnx`, `src/cdx` | orders, tags, CNX/CDX/LMDB |
| Memo | `src/memo` | MemoManager lifecycle |
| Expression | `src/xexpr`, `src/cli/expr` | xexpr and function bridge |
| Relations / tuple | workspace/relation/tuple CLI files | workspace, relations, tuple traversal |
| Browser/TUI | `src/browser`, `src/tv` | projection and UI |
| Bindings | `src/bindings` | optional external integration |
| Common | `src/common` | path state and shared helpers |

## Core rule

Source verifies ownership, handlers, build gates, provenance, and implementation boundaries. HELP and META provide mined evidence. CMDHELPCHK validates reflection. Runtime proof proves behavior. The manuals assemble the result.

---

# DEV-04 Architecture Overview

```yaml
page_id: DEV-04
title: Architecture Overview
status: DRAFT
last_verified: 2026-05-24
```

## Two interlocked architectures

```text
Runtime architecture
  command, data, logic, projection, storage, workspace, browser, and binding behavior

SelfDoc architecture
  HELP, META, CMDHELPCHK, source verification, runtime proof, diagrams, and manuals
```

## Four-layer runtime model

```text
Command Layer
Data Layer
Logic Layer
Projection Layer
```

## Open architecture doctrine

The runtime is intentionally open in several places. Those seams are part of
the product design, not accidental side effects.

Current architecture lanes that should remain visible:

- open index work, including INX, CNX, CDX, LMDB, and student/lab index
  experiments such as SCX and SIX
- workbench front ends that consume runtime truth rather than replacing it,
  including CLI, TUI, wx workbench, and Python preview lanes
- custom command and function extension lanes, where centrally owned built-ins
  stay governed while student/local surfaces can be added through controlled
  registration paths
- polling, trigger, and lifecycle hook surfaces that allow observation and
  extension around command execution and runtime state changes
- educational hooks where the system is used as a teaching engine rather than a
  sealed appliance

Practical rule:

- the engine owns database truth
- front ends, browsers, and portals consume that truth
- help, metadata, SelfDoc, and manuals describe and validate that truth

## Architecture seam families

```text
Command and function seams
  built-in registration, aliases, controlled extension lanes

Index seams
  INX / CNX / CDX / LMDB / educational local-index labs

Projection seams
  LIST, BROWSE, ERSATZ, tuple views, GUI/TUI consumers

Lifecycle seams
  polling, triggers, diagnostics, runtime observation

Documentation seams
  HELP, META, CMDHELPCHK, SelfDoc, diagrams, manuals, website
```

## Workbench rule

GUI, TUI, and browser-like workbench layers must not invent their own
database-truth model.

They should consume:

- cursor and order state
- relation state
- mutation outcomes
- validation and diagnostic outcomes
- command/session state

from DotTalk++ and the engine, then project that state in a form suitable for
teaching, browsing, or application work.

## Architecture canaries

- SET ORDER/CNX tag availability and reporting consistency.
- x64 ERSATZ load reporting inconsistency.
- WORKSPACE OPEN DBF memo backend auto-attach gap.
- MIN/MAX scalar function versus aggregate command ambiguity.
- AGGS scaffold/debug command exposure.
- SYSFUNC empty.
- SOURCE_MINER rows require review.

## Short form

DotTalk++ is a visible database runtime whose documentation and metadata systems are themselves part of the architecture.

---

# DEV-05 Command System

```yaml
page_id: DEV-05
title: Command System
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Scope

This is the command-system architecture and workflow chapter. It is not a
replacement for the generated command reference, but it no longer needs to wait
for a hypothetical future crosswalk before describing the real current system.

## Current command authority stack

For a command that exists today, authority flows in this order:

1. runtime behavior
2. source command implementation and usage contract
3. HELP surfaces built from those contracts
4. `dotref.hpp` / `foxref.hpp` catalog layers
5. manuals and website prose

Practical meaning:

- runtime proves that a command exists and behaves a certain way
- source owns the usage contract and implementation truth
- HELP explains the command to users
- `dotref.hpp` and `foxref.hpp` are curated reference-header catalogs, not the
  implementation layer
- manuals summarize and connect the lanes; they do not invent command truth

## Reference-header policy

`dotref.hpp` is the canonical DotTalk++ command catalog layer for commands that
are implemented and intentionally surfaced in the current system.

`foxref.hpp` is the historical/classic support catalog layer. When a Fox-family
command has a real `cmd_*.cpp` implementation, its `foxref.hpp` entry should be
kept aligned with DotTalk++ reality rather than pretending to be an untouched
FoxPro clone.

Working rule:

- if a command has real code, the relevant reference-header entry should match
  current supported syntax and intent
- if source and reference headers disagree, source/runtime win until the header
  is repaired
- if manuals disagree with source/help/reference, manuals are wrong and must be
  repaired

## Command manual pipeline

```text
source usage contract / runtime registration
  -> HELP command/topic/artifact evidence
  -> META semantic catalog where seeded
  -> CMDHELPCHK validation
  -> source handler/build verification
  -> runtime proof
  -> command crosswalk
  -> Developer Manual
  -> User/Student derivations
  -> Website derivations
```

## Surface classes

`PUBLIC`, `DEV_ONLY`, `TRANSITIONAL`, `INTERNAL`, `SCAFFOLD`, `EDUCATIONAL`, `APP`, `ALIAS`, `LEGACY`, `UNKNOWN`.

## Current HELP rebuild rule

Current documented operator order:

1. If `dotref.hpp` changed, run `CMDHELP BUILD LEGACY` first.
2. Run `CMDHELP BUILD . d:\code\ccode\src`.
3. Run `CMDHELPCHK`.
4. Use plain `CMDHELP BUILD` only as the lighter refresh when the source root is
   already implied and no explicit source-root proof is needed.

Reason:

- `CMDHELP BUILD LEGACY` refreshes the classic `commands.dbf` / `cmd_args.dbf`
  path that still depends on the reference-header catalog
- `CMDHELP BUILD . d:\code\ccode\src` is now the richer current HELP DATA pass;
  it harvested `USAGE_CONTRACT` and `SOURCE_MINER` rows in addition to
  `REGISTRY`, `DOTREF`, `FOXREF`, `EDREF`, and `SHARED_MSG`
- `CMDHELPCHK` is the structural validation gate after rebuild

Observed verified run on 2026-07-07:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Observed outcome from that verified run:

- legacy report wrote `447` command rows and `2294` arg rows
- current HELP DATA reported `10846` line rows and `473` topics
- structural checks passed with `OK no structural issues found`

## Current command-family practical rule

The current command family is no longer waiting for a future crosswalk before
it can be described. The real state today is:

- command implementations live in `src/cli`
- command registration binds them into the shell/runtime
- source usage contracts are harvested into HELP
- `REGRESSION` provides curated top-layer shakedown entrypoints
- manuals explain the family after build/runtime/help evidence are in place

## Reflection report interpretation

`CMDHELPCHK` reflection reports are not all the same layer.

Working interpretation:

- `Subcommand Inventory` reflects curated `SET` family subcommands from the
  reference/command-catalog lane
- `Command Inventory` reflects the canonical `command_catalog` slice, not every
  registered shell token
- full command breadth still appears in `CMDHELP BUILD LEGACY`, current HELP
  DATA, shell registration, and reference-header lanes

Practical meaning:

- a short `Command Inventory` report is not automatically a bug
- a mismatched public/internal flag in reflection is a real catalog-policy issue
- if a command is in runtime/help/reference but missing from the canonical
  reflection slice, decide whether that is intentional curation or unharvested
  promotion

## Regression rule for command surfaces

Regression scripts must bootstrap their own environment.

That means a script should begin with lane setup such as:

```text
DO x64
```

or:

```text
DO cmdhelp
```

before it opens tables, workspaces, schemas, or ERSATZ paths.

Working rule:

- if an older script still has value but assumes a caller-owned environment,
  fix it
- if it no longer has value, retire it

## Manual and website derivation rule

The manual and website command prose should both harvest from the same evidence
spine:

- source usage contracts
- runtime proof
- HELP builds
- CMDHELPCHK
- reviewed canaries

Do not copy command truth back from the website into the manual when the source
project already owns that truth.

---

# DEV-06 DotScript

```yaml
page_id: DEV-06
title: DotScript
status: DRAFT
last_verified: 2026-05-24
```

## Identity

DotScript is the canonical automation path for DotTalk++ command sequences. `DO` is an entry into DotScript execution.

## Important setup scripts

```text
do x32
do x64
do cmdhelp
do metadata
mcc / . mcc
```

Observed correction: `do meta` failed; `do metadata` worked.

## Practical rule

Scripts prepare state. Transcripts prove what happened. HELP/META stores record mined evidence. Manuals explain the verified result.

---

# DEV-07 DbArea and Table Engine

```yaml
page_id: DEV-07
title: DbArea and Table Engine
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Core ownership

DbArea owns table runtime state: open table state, records, cursor state, mutation behavior, table flavor behavior, and work-area identity.

DbArea does not own memo payload lifecycle, LMDB physical backend implementation, HELP/META cataloging, browser rendering, TUI display policy, or manual generation.

## Current evidence lanes

- `include/xbase.hpp`
- `src/xbase`
- table command handlers in `src/cli`
- HELP command/topic/artifact rows
- runtime table/work-area smokes

## Future/maturing META feeders

- `SYSFLDDIC`: field dictionary and logical field roles
- `SYSCMD`: table command identity and handlers
- `SYSARGS`: command argument metadata
- `SYSMSG`: table/mutation/navigation messages and errors
- `SYSHELP`: table concept help

## Crosswalk target

`table-command-crosswalk-v0.csv`

---

# DEV-08 DBF x32 / x64 Formats

```yaml
page_id: DEV-08
title: DBF x32 / x64 Formats
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-07-07
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.

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

---

# DEV-09 Indexing: INX, CNX, CDX, LMDB

```yaml
page_id: DEV-09
title: Indexing: INX, CNX, CDX, LMDB
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Core doctrine

CDX is the logical/user-facing multi-tag abstraction. LMDB is the physical backend.

## Open index architecture

Indexing is not treated as a sealed black box.

The current architecture intentionally exposes:

- index attach/open behavior
- rebuild behavior
- order/tag selection
- verification and inspection paths
- educational index-lab experiments

That means the indexing chapter must account for both production-facing and
teaching-facing surfaces.

Current families to preserve clearly:

- `INX` for single-index educational and compatibility work
- `CNX` for x32/VFP-family structural indexing
- `CDX` as the multi-tag logical container
- `LMDB` as the x64 physical backend under CDX
- `SCX` / `SIX` as local or student index-lab seams that demonstrate open
  architecture rather than ordinary production indexing

## Index ownership rule

The index family owns:

- tag metadata
- order traversal behavior
- attach/detach semantics
- rebuild semantics
- verification semantics

Projection layers such as LIST, BROWSE, ERSATZ, GUI, and TUI may demonstrate
ordered traversal, but they do not own index truth.

## Mixed-surface rule

The runtime can teach multiple indexing families without pretending they are all
the same thing.

Manual rule:

- describe canonical runtime indexing honestly
- keep educational/index-lab surfaces visible
- do not flatten `SCX`/`SIX` into the ordinary CNX/CDX/LMDB abstraction
- do not let a browser or GUI description become the authority for index state

## Current practical direction

The intended practical direction is:

- x64 production work prefers CDX plus LMDB backend storage
- x32/VFP compatibility work keeps CNX/IDX-style historical paths visible
- INX remains useful for teaching and timing/sort experiments
- open index APIs and lab commands remain part of the architecture story
  because x64base is meant to be learnable and extendable

## Future/maturing META feeders

- `SYSCMD`: index command identity and handlers
- `SYSSUBCMD`: SET ORDER and related subcommands
- `SYSENTVAR`: aliases, shortcuts, reexpressions
- `SYSARGS`: tag/order/key argument metadata
- `SYSMSG`: index warnings/errors
- `SYSHELP`: index concept help

## SET ORDER canary

Reported active order must agree with actual traversal order before marking an order path PROVEN.

## Crosswalk target

`index-command-crosswalk-v0.csv`

---

# DEV-10 Memo System

```yaml
page_id: DEV-10
title: Memo System
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Current truth

```text
normal USE memo path is proven
workspace/bulk-open memo attach path is canary
MemoManager owns payload lifecycle
DbArea owns record/table context
metadata alignment should mature through SYSFLDDIC, SYSMSG, SYSCMD, SYSARGS, and SYSHELP
```

## Proven path

`USE memo_x64` attaches the memo backend, supports memo REPLACE, and preserves close/reopen readback.

## Canary path

`WORKSPACE OPEN DBF` opens `MEMO_X64.dbf` without memo backend attachment in the observed red path.

## Crosswalk target

`memo-system-crosswalk-v0.csv`

---

# DEV-11 Expression Engine

```yaml
page_id: DEV-11
title: Expression Engine
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Correct evidence rule for functions

SYSFUNC is the future semantic feeder for function metadata. Until it is populated, temporary evidence lanes must be labeled, crosswalked, and designed for later SYSFUNC reconciliation.

## Current temporary evidence lanes

- CMDHELPCHK Function Inventory
- HELP FUNCTION `<name>`
- HELP FUNCTIONS
- function catalog source
- xexpr/function registry source
- runtime expression smokes

## Future preferred META lane

- `META.SYSFUNC`

## Function crosswalk statuses

`PENDING_SYSFUNC_SEED`, `READY_FOR_SYSFUNC_PROMOTION`, `BLOCKED_BY_ARG_CONFLICT`, `BLOCKED_BY_HANDLER_UNKNOWN`, `BLOCKED_BY_RUNTIME_CANARY`, `PROMOTED_TO_SYSFUNC`.

---

# DEV-12 Relations, Workspaces, and Tuple Traversal

```yaml
page_id: DEV-12
title: Relations, Workspaces, and Tuple Traversal
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Current truth

```text
x32 MCC relation/workspace/ERSATZ path is proven
x64 workspace/ERSATZ load reporting is canary
tuple traversal is relation-aware and projection-oriented
FILEID is current reliable SelfDoc join spine
BLOCKID joins are deferred
REL ENUM is a meaningful metadata seed point
```

## Future/maturing META feeders

- `SYSCMD`
- `SYSSUBCMD`
- `SYSENTVAR`
- `SYSARGS`
- `SYSMSG`
- `SYSHELP`
- `SYSFLDDIC`

## Crosswalk targets

- `workspace-relation-crosswalk-v0.csv`
- `tuple-command-crosswalk-v0.csv`
- `relation-proof-ledger-v0.md`

---

# DEV-13 Browsers and TUI

```yaml
page_id: DEV-13
title: Browsers and TUI
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Ownership doctrine

Browser/TUI surfaces render and navigate projected state. They do not own table storage, relation semantics, memo payloads, command truth, or metadata truth.

## Workbench front-end doctrine

This chapter now needs to be read as part of the broader workbench/front-end
architecture.

Relevant front-end families include:

- classic CLI projection surfaces
- TUI/browser surfaces
- ERSATZ and relation-aware result browsing
- wx workbench lanes
- Python preview/prototyping lanes
- campus/lab portal consumers

All of them are consumers of runtime truth.

They should consume:

- area selection and cursor state
- logical order state
- relation state
- tuple/projection state
- mutation and validation outcomes
- message and diagnostics output

from DotTalk++ and the engine.

They should not:

- invent their own database truth
- replace runtime relation semantics
- redefine index/order ownership
- become the source of command or metadata truth

## Open architecture implications

The browser/TUI/front-end family is one of the main public proofs that x64base
is an open architecture.

That means this chapter should preserve the distinction between:

- front ends as views over engine truth
- extension seams that allow new workbench surfaces to be built
- educational work that uses those surfaces to teach data navigation,
  projection, ordering, and relation traversal

## Current practical lesson

The strongest current lesson is that a front end should mirror runtime truth
rather than clone it.

That rule applies equally to:

- ERSATZ
- relation result browsers
- TUI lanes
- wx workbench
- Python preview

When those layers drift from runtime state, the runtime wins and the front end
must be repaired.

## Proven paths

- x32 MCC / ERSATZ relation browser path.
- plain ERSATZ/no-arg browser path.
- LIST as traversal proof surface.

## Canaries

- x64 workspace/ERSATZ load reporting inconsistency.
- ERSATZ GRID snapshot branch deferred.
- memo projection may show raw pointers if backend is unattached.
- TUI availability may be build-gated.

## Future/maturing META feeders

- `SYSCMD`
- `SYSSUBCMD`
- `SYSENTVAR`
- `SYSARGS`
- `SYSMSG`
- `SYSHELP`

---

# DEV-14 HELP, Metadata, and CMDHELPCHK

```yaml
page_id: DEV-14
title: HELP, Metadata, and CMDHELPCHK
status: DRAFT
last_verified: 2026-07-08
```

## Center of gravity

HELP and META are not side documentation. They are mined SelfDoc evidence stores
used by the documentation family.

The important correction is that this family is no longer just:

```text
source -> CMDHELP -> manual
```

It is now understood as a layered producer stack:

- source and curated reference headers define the candidate truth inventory
- HELP DATA and legacy HELP lanes explain and preserve command surfaces
- CMDHELPCHK validates reflected structure and catalog drift
- `dt_meta.lib` and `metacollect.exe` harvest read-only metadata facts outside
  the shell runtime
- `manualgen.py` assembles inventory, validation, manifests, and publication
  workspaces from the same evidence spine

That distinction matters because manuals and website pages must derive from the
same reviewed evidence set without pretending that one tool does every job.

## Core doctrine

Use this doctrine consistently:

- runtime proves behavior
- source defines implementation and subsystem ownership
- HELP explains command behavior, vocabulary, examples, and concepts
- metadata organizes identities, arguments, ownership, and relationships
- CMDHELPCHK validates structural alignment and catches drift
- SelfDoc preserves provenance and evidence lineage
- manualgen assembles reviewable publication artifacts

Safe wording:

- HELP/META/CMDHELPCHK-first is assembly order
- it is not authority order
- source is not demoted to a sidecar
- runtime proof is still required for behavior claims

Verified HELP DATA rebuild on 2026-07-07 used:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Observed current HELP DATA evidence from that verified run:
- line rows: `10846`
- topics: `473`

Observed legacy compatibility evidence from that verified run:
- `commands.dbf` rows written: `447`
- `cmd_args.dbf` rows written: `2294`

Observed META evidence:
- META.SYSCMD: 40 records
- META.SYSSUBCMD: 12 records
- META.SYSENTVAR: 12 records
- META.SYSFUNC: 0 records in the observed seed
- META.SYSHELP: 8 records

Observed release-build documentation toolchain outside `dottalkpp`:

- `dt_meta.lib`
- `metacollect.exe`

Observed manual assembly toolchain:

- `tools/manualgen/manualgen.py`

## HELP tables

`CMD_ARGS`, `COMMANDS`, `HELP_ARTIFACTS`, `HELP_LINE`, `HELP_SECTION`, `HELP_TOPIC`.

## META tables

`SYSARGS`, `SYSCMD`, `SYSENTVAR`, `SYSFLDDIC`, `SYSFUNC`, `SYSHELP`, `SYSMSG`, `SYSSUBCMD`.

## CMDHELPCHK role

CMDHELPCHK validates reflected command/function metadata and HELP artifact paths.

Observed result from the verified 2026-07-07 run:

```text
Structural Checks
=================
OK no structural issues found
```

## Practical rebuild rule

Current practical order is:

1. `CMDHELP BUILD LEGACY` when `dotref.hpp` changed
2. `CMDHELP BUILD . d:\code\ccode\src` for the richer current HELP DATA pass
3. `CMDHELPCHK` to validate reflected structure

The explicit source-root build is important because it harvested:

- `REGISTRY`
- `DOTREF`
- `FOXREF`
- `EDREF`
- `SHARED_MSG`
- `SOURCE_MINER`
- `USAGE_CONTRACT`

## Producer roles

### HELP lane

HELP is the strongest explanatory feeder.

It explains:

- command vocabulary
- usage shapes
- examples
- operator concepts
- artifact lineage now stored in HELP DATA

HELP can be broad and richly populated without proving runtime behavior.

### Metadata lane

Metadata organizes the system semantically.

It is the right lane for:

- command identity
- argument identity
- message identity
- environment variables
- feeder relationships
- future diagram and website attachment points

Sparse metadata is not the same as failed metadata. Sparse tables are future
feeders until seeded and verified.

### CMDHELPCHK lane

CMDHELPCHK is a validator, not a behavior proof engine.

It is responsible for:

- structural reflection checks
- HELP/catalog drift checks
- artifact validation
- manual assembly gates where reflected structure matters

### External metadata lane

The release build proves there are documentation producers outside the shell:

- `dt_meta.lib` supplies read-only extraction support
- `metacollect.exe` is the standalone developer entrypoint for metadata/source
  extraction, compare reports, and seed-export CSV generation

These belong in the documentation family and must not be hidden behind a
runtime-only mental model.

### Manualgen lane

`manualgen.py` assembles inventories, validation reports, manifests, dry-run
artifacts, and publication workspaces.

Its role is assembly, not authority replacement.

## Runtime inspection surfaces for the documentation family

The documentation family now has real runtime inspection and teaching surfaces.
The manual should coordinate with them instead of describing the lanes as if
they only exist in reports.

- `MANUAL` is the read-only runtime inspector over accepted `MAN*` manualgen
  catalog state
- `DDICT` is the read-only runtime inspector over the active Data Dictionary
  catalog, including fields, tags, relations, and evidence
- `BBOX` is the educational blackbox/teaching surface for comments, HELP,
  manualgen, datadict, messaging, maintenance, and contracts
- `MAINT` is the read-only maintenance/control-surface inspector for lane
  status, docs, GUI, AI Friendly, and contracts

That split is important:

- `MANUAL` inspects accepted manual-catalog state
- `DDICT` inspects accepted catalog metadata state
- `BBOX` teaches the model
- `MAINT` reports the management surface

Supporting crosswalk:

```text
docs/manuals/developer/manualgen/reports/manual_family_runtime_surface_crosswalk_v1.md
```

## Mutation boundaries

These lanes must stay role-clean:

- HELP build mutates HELP DATA and legacy HELP compatibility lanes only when
  explicitly invoked
- CMDHELPCHK is report-only
- `dt_meta.lib` and `metacollect.exe` are read-only/report-only by contract
- `manualgen.py` writes reports and manual artifacts, not runtime HELP/META
  production data

This boundary keeps publication work from silently mutating runtime truth.

## Crosswalk artifacts

Current working crosswalks:

```text
docs/manuals/developer/manualgen/reports/help_meta_toolchain_crosswalk_v1.csv
docs/manuals/developer/manualgen/reports/help-topic-to-manual-section-map-v1.csv
docs/manuals/developer/manualgen/reports/help-topic-to-website-section-map-v1.csv
docs/manuals/developer/manualgen/reports/manualgen-evidence-harvest-checklist-v1.md
```

Current concrete messaging/publication artifact now added:

```text
docs/manuals/developer/manualgen/reports/shared-message-to-surface-map-v1.csv
```

Use them in this order:

1. toolchain crosswalk to identify producer roles
2. topic-to-section map to place families into manual chapters
3. evidence harvest checklist to repeat the rebuild/validation sequence

## Central rule

HELP is broad and richly populated. META is semantic and seeded but narrower.
CMDHELPCHK validates reflected structure. Source verifies. Runtime proves.

---

# DEV-15 SelfDoc Pipeline

```yaml
page_id: DEV-15
title: SelfDoc Pipeline
status: DRAFT_PATCHED
last_verified: 2026-07-08
```

## Corrected pipeline

```text
source usage contracts / command registration / shared messages
  -> CMDHELP BUILD LEGACY (when dotref changes)
  -> CMDHELP BUILD . d:\code\ccode\src
  -> HELP DATA + legacy command catalogs
  -> META semantic catalogs where seeded
  -> CMDHELPCHK validation
  -> source / command / CMake verification sidecars
  -> runtime proof classification
  -> evidence binder
  -> diagrams / metadata crosswalks
  -> Developer Manual
  -> User Manual and Student Manual derivations
  -> Website derivations
```

This is still an assembly pipeline, not a truth-authority inversion.

The governing doctrine remains:

- runtime proves
- source defines
- HELP explains
- metadata organizes
- CMDHELPCHK validates
- SelfDoc preserves provenance
- manualgen assembles

## Pipeline manifests and policy homes

Current SelfDoc control artifacts already in-tree:

```text
selfdoc/pipeline_manifest.yaml
selfdoc/tool_manifest.yaml
selfdoc/SELFDOC_ARTIFACT_LIFECYCLE_POLICY_v0.md
selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md
```

These matter because SelfDoc is no longer just a loose idea. It has explicit
manifest and policy files that describe:

- pipeline stages
- helper-tool roles
- lifecycle classes
- safety classes
- non-mutation guards

## Manifested report-only doctrine

The current `selfdoc/pipeline_manifest.yaml` declares the metadata collection
pipeline as:

- active
- report-only
- default

Its reviewed stages include:

- `metacollect_facts_scan`
- `metacollect_compare_scan`
- `metacollect_sysfunc_candidate_export`
- `metacollect_sysargs_candidate_export`

And its non-mutation guards explicitly include:

- no DBF writes
- no HELP rebuild
- no CMDHELPCHK changes
- no source repairs
- no live metadata promotion
- review before import

That is the correct posture for SelfDoc.

## SelfDoc mission

SelfDoc exists to keep DotTalk++ from becoming three different realities: what source says, what HELP says, and what runtime does.

The current system extends that rule upward:

- source/runtime own behavior truth
- HELP and reference layers explain and reflect that truth
- META organizes semantic crosswalks where seeded
- manuals and website prose derive from the same evidence spine

The website is not an authority override for runtime/manual truth. It is an
attached publication lane that should harvest from the same evidence stack.

## Verified operator sequence

Verified on 2026-07-07:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Observed result:

- legacy compatibility layer refreshed
- current HELP DATA incorporated `REGISTRY`, `DOTREF`, `FOXREF`, `EDREF`,
  `SHARED_MSG`, `SOURCE_MINER`, and `USAGE_CONTRACT`
- structural validation passed
- external metadata helpers remained outside live HELP/META authority

## Lifecycle and safety classes

The current SelfDoc artifact policy defines these lifecycle classes:

```text
CANONICAL
GENERATED
EVIDENCE
PROBE
CANDIDATE
PROMOTED
ATTIC
TRANSIENT
NOISE
QUARANTINE
```

And these safety classes:

```text
READ_ONLY
REPORT_ONLY
PLAN_ONLY
PROJECTION_WRITER
PATCH_WRITER
MUTATION_TOOL
```

Current SelfDoc build work is intentionally constrained to the safe/reporting
end of that range. This is the project's defense against documentation lanes
quietly mutating runtime truth.

## Authority rule

Within the SelfDoc pipeline, authority flows in this order:

1. runtime behavior
2. source implementation and source usage contract
3. HELP/reflection/reference output
4. META semantic organization where seeded
5. manual and website prose

If upper layers disagree with lower layers, the upper layer is wrong until it is
repaired.

## External tool intake rule

SelfDoc now has an explicit rule for external programs.

External tools:

- may assist
- may harvest
- may compare
- may emit candidate CSVs or reports
- are not authority by default

`metacollect` is the model case:

- it is a read-only source/catalog scanner
- it normalizes future metadata candidates
- it emits facts, compare reports, and import candidates
- it does not replace live metadata DBFs
- it does not rebuild HELP
- it does not replace `CMDHELPCHK`
- it does not publish manuals

So the larger family is:

```text
source/runtime/help
  -> metacollect (read-only normalize/compare/propose)
  -> reviewed import candidates
  -> live metadata DBFs
  -> SelfDoc / manualgen / diagram promotion lanes
```

This is the right shape because it keeps proposal tooling separate from live
authoritative mutation.

## Practical consequences

When working in SelfDoc:

- inventory first
- classify second
- promote third
- automate fourth
- mutate only after explicit review

That rule is already written into the artifact lifecycle policy and should stay
visible in the manual because it governs how we grow the system without losing
authority discipline.

## MANUALCHK relationship

MANUALCHK is planned. CMDHELPCHK validates command/help/reflection congruence. MANUALCHK should later validate manual/evidence congruence.

## Current bridge to manualgen

SelfDoc does not replace manualgen and manualgen does not replace SelfDoc.

Current relationship:

- SelfDoc preserves provenance, manifests, probes, and evidence governance
- manualgen consumes reviewed evidence to assemble manual inventories,
  validation reports, manifests, and publication workspaces

The manual/website layer should therefore consume from SelfDoc-governed
evidence, not invent a parallel prose-only truth.

---

# DEV-16 Smoke Tests and Canaries

```yaml
page_id: DEV-16
title: Smoke Tests and Canaries
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Canary classes

- Runtime canaries
- HELP/META evidence canaries
- Manual-generation canaries
- Publication-lane canaries

## Proof levels

`OBSERVED`, `SCRIPTED`, `VALIDATED`, `REGRESSION`, `CATALOGED`.

CATALOGED is not the same as PROVEN.

## Current regression rule

Regression scripts are expected to bootstrap their own environment.

Practical rule:

- start by setting the lane, for example `DO x32`, `DO x64`, `DO cmdhelp`, or
  `DO metadata`
- then open tables, workspaces, schemas, or ERSATZ paths
- if an older script still has value but assumes caller-owned state, fix it
- if it no longer has value, retire it

The curated `REGRESSION` launcher is not meant to expose every historical
DotScript. It is the stable top-layer entrypoint for reviewed regression
surfaces.

## Current documentation canary stack

For command/reference/help drift, the current verified canary stack is:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Verified 2026-07-07 outcome:

- legacy compatibility rows refreshed
- current HELP DATA harvested `REGISTRY`, `DOTREF`, `FOXREF`, `EDREF`,
  `SHARED_MSG`, `SOURCE_MINER`, and `USAGE_CONTRACT`
- structural validation passed

## Named current canary examples

- `dottalkpp/data/scripts/canaries/x64_matrix_metrics_boundary_canary.dts`
- curated `REGRESSION HARVEST` top-layer shakedown
- reflection/public-surface checks via `CMDHELPCHK`

## Standing canary rules

- HELP breadth is not behavior proof.
- META absence is not project absence.
- SOURCE_MINER inference is not public documentation.
- Runtime proof is path-specific.
- Canaries remain visible until closed with evidence.
- Website/manual polish is not authority by itself.

---

# DEV-17 Contributor Rules

```yaml
page_id: DEV-17
title: Contributor Rules
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Done definition

A change is not done until source, HELP, META, CMDHELPCHK, runtime proof, canaries, manual evidence, and AUTOLOG are all checked or explicitly marked pending/canary.

## Core rule

```text
If you change behavior, update evidence.
If you change evidence, verify behavior.
If you write the manual, cite the evidence.
If something disagrees, create a canary or gap report.
```

## Current command/help refresh rule

If a command surface, usage contract, or reference-header catalog changed, the
current default operator sequence is:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Practical meaning:

- `CMDHELP BUILD LEGACY` keeps the classic `commands.dbf` / `cmd_args.dbf` lane
  synchronized when `dotref.hpp` changed
- the explicit source-root build refreshes the richer HELP DATA lane
- `CMDHELPCHK` is the structural gate after rebuild

## Regression maintenance rule

If a regression DotScript is still useful:

- make it bootstrap its own environment
- keep it curated under stable regression entrypoints
- prefer promotion into the `REGRESSION` launcher over leaving it as
  unclassified historical debris

If it is no longer useful, retire it instead of leaving a misleading script in
place.

## Report-first safety boundary

Safe default actions: read evidence, produce inventories, produce crosswalks, produce gap reports, produce diagrams, produce manual drafts.

Actions requiring explicit authorization: mutate HELP DBFs, mutate META DBFs, rewrite source comments, change CMDHELPCHK behavior, change classifier policy, rebuild HELP DATA, or change public/internal surface classification.

---

# DEV-18 Known Red Paths

```yaml
page_id: DEV-18
title: Known Red Paths
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Runtime canaries

| ID | Status | Summary |
|---|---|---|
| CAN-001 | OPEN | SET ORDER/CNX tag availability and reporting consistency. |
| CAN-002 | OPEN | x64 ERSATZ load reports failure while browser state appears usable. |
| CAN-003 | OPEN | WORKSPACE OPEN DBF memo backend auto-attach gap. |
| CAN-004 | OPEN | MIN/MAX scalar function versus aggregate command ambiguity. |
| CAN-005 | OPEN | AGGS scaffold/debug command exposure. |
| CAN-006 | DEFERRED | ERSATZ GRID snapshot branch deferred. |
| CAN-007 | DEFERRED | BLOCKID-level SelfDoc joins deferred; FILEID is reliable. |

## HELP/META evidence canaries

| ID | Status | Summary |
|---|---|---|
| HM-CAN-001 | OPEN | HELP broad / META narrow asymmetry. |
| HM-CAN-002 | OPEN | SYSFUNC empty. |
| HM-CAN-003 | REVIEW | SYSSUBCMD seed hygiene. |
| HM-CAN-004 | REVIEW | SYSENTVAR seed hygiene. |
| HM-CAN-005 | REVIEW | SYSHELP narrow seed. |
| HM-CAN-006 | OPEN | AGGS public/internal classification conflict. |
| HM-CAN-007 | REVIEW | SOURCE_MINER inferred rows require review. |

## Publication/manual canaries

| ID | Status | Summary |
|---|---|---|
| PUB-CAN-001 | OPEN | Combined developer manual can drift from per-section chapter files if mirrored updates are not pushed upward after verified edits. |

---

# DEV-19 HELP/META Crosswalk and Manual Generation

```yaml
page_id: DEV-19
title: HELP/META Crosswalk and Manual Generation
status: DRAFT
last_verified: 2026-07-07
```

## Working rule

```text
Rebuild HELP from source and reference layers.
Read HELP broadly.
Read META semantically where seeded.
Validate with CMDHELPCHK.
Verify with source.
Prove with runtime.
Assemble manuals and website from the same evidence spine.
```

## Verified rebuild path

Current verified rebuild path:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Interpretation:

- `CMDHELP BUILD LEGACY` refreshes the classic `commands.dbf` / `cmd_args.dbf`
  lane when `dotref.hpp` changed
- `CMDHELP BUILD . d:\code\ccode\src` is the richer current HELP DATA pass
- `CMDHELPCHK` validates reflected structure after rebuild

The explicit source-root build harvested:

- `REGISTRY`
- `DOTREF`
- `FOXREF`
- `EDREF`
- `SHARED_MSG`
- `SOURCE_MINER`
- `USAGE_CONTRACT`

## Crosswalk purpose

The HELP/META crosswalk is not meant to replace source authority.

Its job is to:

- bind HELP topics and artifacts to semantic metadata lanes
- record what is already seeded versus what is still sparse
- keep manualgen/manual/website assembly from inventing parallel truth
- support diagrams and attached publication lanes without copying truth
  sideways

## Publication rule

Manuals and website pages should both derive upward from the same reviewed
evidence set.

Working rule:

- do not copy runtime/manual command truth back from the website
- do not let website prose become the only copy of technical truth
- when a page is not directly derived from the source project, mark it as prose
  or publication-only material

## Proposed crosswalk schema

```csv
key,kind,help_command,help_cmdkey,help_topic,help_topickey,help_status,help_implemented,help_supported,help_primary,help_confid,artifact_sources,artifact_kinds,artifact_confids,artifact_severities,meta_table,meta_id,meta_name,meta_active,meta_public,meta_dispatch_reachable,meta_handler,cmdhelpchk_status,source_file,source_owner,build_gate,proof_status,proof_id,canary_id,manual_target,derived_user_target,derived_student_target,review_status,notes
```

## Required next artifacts

```text
help-meta-crosswalk-v0.csv
help-meta-gap-report-v0.md
function-crosswalk-v0.csv
command-surface-classification-v0.md
source-miner-review-v0.md
seed-hygiene-report-v0.md
```

## Current practical next artifacts

After the verified 2026-07-07 rebuild, the most useful next pieces are:

```text
help-topic-to-manual-section-map-v1.csv
help-topic-to-website-section-map-v1.csv
shared-message-to-surface-map-v1.csv
metadata-diagram-attachment-plan-v1.md
manualgen-evidence-harvest-checklist-v1.md
```

Current concrete artifact path now added:

```text
docs/manuals/developer/manualgen/reports/manualgen-evidence-harvest-checklist-v1.md
```

## Producer/toolchain crosswalk

The documentation family is not just `source -> CMDHELP -> manual`.

It includes distinct producers and validators outside the runtime shell:

- curated reference headers: `dotref.hpp`, `foxref.hpp`, `edref.hpp`
- embedded source contracts: `@dottalk.usage`
- HELP DATA harvesting and bridge code
- runtime builder/reporter: `CMDHELP`
- runtime validator: `CMDHELPCHK`
- external metadata toolchain: `dt_meta.lib` + `metacollect.exe`
- python publication lane: `tools/manualgen/manualgen.py`

Current concrete artifact path now added:

```text
docs/manuals/developer/manualgen/reports/help_meta_toolchain_crosswalk_v1.csv
```

Additional seeded family-to-section map:

```text
docs/manuals/developer/manualgen/reports/help-topic-to-manual-section-map-v1.csv
docs/manuals/developer/manualgen/reports/help-topic-to-website-section-map-v1.csv
```
