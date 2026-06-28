# Help, Message, and Reference Authority Model v1

Status: canonical draft  
Subsystem: HELP / messaging / reference headers / metadata / selfdoc  
Working area: `D:\code\ccode\dottalkpp`  
Mutation authority: none from this document alone  

## Purpose

This document defines a concrete source-of-truth model for these surfaces:

- compiled fallback message catalog in `src/help/helpdata_messages.*`
- runtime message catalog loader in `src/help/message_catalog.cpp`
- command/function reference headers `include/dotref.hpp` and `include/foxref.hpp`
- HELP/CMDHELP rows and generated help artifacts
- metadata feeders such as `SYSCMD`, `SYSFUNC`, `SYSARGS`, and `SYSMSG`
- SelfDoc/manualgen/metacollect consumers of those lanes

The goal is to stop treating large generated code files as primary authoring
surfaces while still preserving bootstrap safety, runtime resilience, and
cross-platform packaging.

## Current Size Snapshot

As of 2026-06-27:

- `src/help/helpdata_messages.cpp`: about 427 KB, 10,178 lines
- `src/help/helpdata_messages.hpp`: about 31 KB, 1,063 lines
- `include/dotref.hpp`: about 41 KB, 670 lines
- `include/foxref.hpp`: about 35 KB, 597 lines

Interpretation:

- `dotref.hpp` and `foxref.hpp` are still manageable in size.
- `helpdata_messages.cpp` is still operationally manageable, but it is already
  large enough that it should be treated as a generated fallback artifact, not
  a hand-maintained authority surface.

## Core Doctrine

Implementation authority, metadata authority, generated artifact authority, and
runtime override authority are not the same thing.

The system must preserve all four roles:

1. source code remains implementation authority
2. DBF/workspace metadata becomes the canonical authoring lane where practical
3. generated headers/code remain build/runtime artifacts
4. runtime can load schema-backed overrides, but must survive without them

That means HELP/META/CMDHELPCHK-first may be a practical assembly workflow, but
it is not the truth-authority doctrine by itself.

## Authority Matrix

| Surface | Current operational authority | Target canonical authority | Why |
|---|---|---|---|
| Runtime command behavior | `cmd_*.cpp`, parser, engine code, supporting libs | same | Source is implementation truth. |
| Runtime function behavior | function implementation, expression engine, helpers | same | Source is implementation truth. |
| Built-in message fallback text | `helpdata_messages.*` | generated from messaging workspace | Startup and failure paths need compiled fallback text. |
| Runtime localized message text | active messaging DBF workspace loaded by `message_catalog.cpp` | messaging workspace | Locale-aware runtime text should come from data when available. |
| Command identity metadata | mixed source/header/manual evidence today | `SYSCMD` and `SYSSUBCMD`, seeded from source contracts | Commands need one metadata home. |
| Function identity metadata | sparse today | `SYSFUNC`, seeded from source contracts and function inventory | Functions need one metadata home. |
| Argument metadata | mixed usage contracts today | `SYSARGS` | Argument shape belongs in metadata, not scattered prose only. |
| Message identity metadata | sparse future feeder today | `SYSMSG` | Message ids, owner, severity, visibility, source crosswalk belong here. |
| HELP rows | evidence/publication layer | generated from source contracts + metadata + curated prose | HELP should not become implementation authority. |
| `dotref.hpp` / `foxref.hpp` | manually curated compatibility/reference headers | generated reference headers | They are useful runtime/reference artifacts, but should not remain primary authoring surfaces forever. |

## Recommended Canonical Model

### 1. Messages

#### Current operational model

- `src/help/helpdata_messages.*` contains the compiled baseline catalog.
- `src/help/message_catalog.cpp` looks for active runtime messaging data under:
  - `dottalkpp/data/messaging`
  - or `dottalkpp/data/dbf/messaging`
- It expects runtime artifacts such as:
  - `SYSTEM_MESSAGES.dbf`
  - `SYSTEM_MESSAGE_TEXT.dbf`
  - `SYSTEM_MESSAGE_TEXT.dtx`
- If runtime messaging artifacts are present, they override by symbol+locale.
- If they are absent or incomplete, the compiled fallback remains available.

#### Target authority

- Canonical message authoring surface:
  - messaging workspace tables
  - especially `SYSTEM_MESSAGES` and `SYSTEM_MESSAGE_TEXT`
  - compact feeder/crosswalk lane: `SYSMSG`
- Generated artifact:
  - `helpdata_messages.hpp`
  - `helpdata_messages.cpp`
- Runtime load order:
  1. compiled fallback English catalog
  2. runtime messaging workspace override
  3. locale fallback chain

#### Policy

- Do not require DBF/schema availability just to print startup, parse, usage,
  or recovery messages.
- Do not hand-maintain `helpdata_messages.cpp` indefinitely as the primary
  authoring surface.
- Do maintain a compiled fallback so:
  - early startup works
  - broken data roots still report intelligibly
  - tests and tools can run without seeded runtime catalogs
  - packaging remains simple and cross-platform

#### Reviewed runtime seed path

The current reviewed snapshot workflow for the active runtime message catalog is
documented in:

- `D:\code\ccode\dottalkpp\docs\messaging\RUNTIME_MESSAGE_CATALOG_SEED_WORKFLOW_v1.md`

That workflow uses:

- generator: `dottalkpp/tools/help/generate_runtime_message_catalog_seed_v1.py`
- import snapshots:
  - `dottalkpp/data/scripts/messaging/SYSTEM_MESSAGES_IMPORT_v1.csv`
  - `dottalkpp/data/scripts/messaging/SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv`
- reviewed scripts:
  - `dottalkpp/data/scripts/messaging/RUNTIME_MESSAGE_CATALOG_IMPORT_v1.RUN_REVIEWED.dts`
  - `dottalkpp/data/scripts/messaging/RUNTIME_MESSAGE_CATALOG_IMPORT_v1.verify.dts`

### 2. Command and Function Reference

#### Current operational model

- `include/dotref.hpp` and `include/foxref.hpp` are consumed by help-resolution
  logic such as `include/browser/cmd_help_resolver.hpp`.
- They are still useful because they provide:
  - searchable catalogs
  - aliases
  - a compatibility layer
  - a legacy/help bridge

#### Target authority

- Implementation truth:
  - `src/cli/cmd_*.cpp`
  - function implementations
  - usage contracts in source headers/comments
- Canonical metadata homes:
  - `SYSCMD`
  - `SYSSUBCMD`
  - `SYSFUNC`
  - `SYSARGS`
- Generated artifacts:
  - `dotref.hpp`
  - `foxref.hpp`

#### Policy

- `dotref.hpp` and `foxref.hpp` should remain compiled/runtime reference
  artifacts.
- They should stop being the long-term place where command/function truth is
  hand-edited first.
- Any command/function with a real implementation should have:
  - source usage contract
  - metadata row
  - generated reference/header presence if part of the public or compat surface

### 3. HELP

HELP is an evidence and publication layer, not implementation authority.

Its job is to assemble:

- command syntax
- argument help
- examples
- sections
- locale-aware public documentation
- artifact attachments and references

HELP should be generated from:

1. source contracts
2. metadata tables
3. curated prose/manual material
4. runtime evidence where appropriate

HELP should not be treated as the primary owner of command semantics.

### 4. SelfDoc / Metacollect / Manualgen

These are downstream consumers and crosswalk builders.

Their role is to:

- inventory
- compare
- crosswalk
- prove
- publish

They must not silently promote generated outputs into implementation truth.

Their preferred upstream inputs should be:

- source contracts
- metadata tables
- HELP evidence
- runtime proof

not hand-maintained generated files as first authority.

## What Is Canonical, By Lane

### Message lane

Canonical authoring target:

- `SYSTEM_MESSAGES`
- `SYSTEM_MESSAGE_TEXT`
- `SYSMSG` crosswalk/identity lane

Generated/runtime artifacts:

- `helpdata_messages.*`
- active runtime message catalog indexes and LMDB

### Command lane

Canonical authoring target:

- source usage contracts in `cmd_*.cpp`
- `SYSCMD`
- `SYSSUBCMD`
- `SYSARGS`

Generated/runtime artifacts:

- `dotref.hpp`
- HELP command rows
- generated command pages

### Function lane

Canonical authoring target:

- source function inventory/contracts
- `SYSFUNC`
- `SYSARGS` where function arguments are modeled

Generated/runtime artifacts:

- `foxref.hpp` where classic compatibility applies
- `dotref.hpp` where DotTalk++ surface applies
- HELP function rows

## Interim Workflow: What To Do Today

Until the metadata lanes are fully seeded and the generators exist, use this
operational sequence:

1. Change source implementation first.
2. Update source usage contract/header contract in the same file.
3. If public command/function wording changed, update the relevant reference
   header as a temporary bridge.
4. Rebuild HELP from the appropriate lane:
   - `cmdhelp build legacy` when `dotref.hpp` / `foxref.hpp` changed materially
   - `cmdhelp build . <source dir>` when source contracts/comments changed
5. Crosswalk into metadata lanes:
   - `SYSCMD`
   - `SYSFUNC`
   - `SYSARGS`
   - `SYSMSG`
6. Publish through HELP/manualgen/selfdoc only after source and metadata agree.

This is an interim operational workflow, not the final authority design.

## Target Workflow: Where We Should End Up

### Messages

1. Author or edit message rows in messaging workspace tables.
2. Generate compiled fallback `helpdata_messages.*` from canonical messaging data.
3. Seed or refresh runtime messaging workspace/indexes.
4. Runtime loads schema-backed messages when available, else compiled fallback.

### Commands and functions

1. Author implementation and usage contracts in source.
2. Harvest into canonical metadata tables.
3. Generate `dotref.hpp` and `foxref.hpp` from metadata plus vetted source
   crosswalk rules.
4. Build HELP from source + metadata + curated prose.
5. Let selfdoc/manualgen/metacollect consume those aligned lanes.

## Why We Still Need Compiled Fallback Surfaces

Do not remove compiled fallback message/reference surfaces yet.

They still solve real problems:

- bootstrap before workspaces are open
- readable failure when the data root is damaged
- cross-platform packaging without mandatory seeded catalogs
- simple test execution
- stable runtime behavior in staging/distribution snapshots

So the right move is not:

- "replace compiled surfaces with schema-only runtime loading"

The right move is:

- "make schema lanes canonical, but keep generated compiled fallback artifacts"

## Specific Concerns and Decisions

### `helpdata_messages.*`

Decision:

- keep compiled
- stop treating it as primary authoring surface
- generate it from messaging workspace authority when the generator is ready

### `dotref.hpp`

Decision:

- keep compiled and searchable
- continue using it as a bridge surface for now
- move long-term authority to source contracts + `SYSCMD`/`SYSARGS`
- generate it later

### `foxref.hpp`

Decision:

- keep compiled and searchable
- keep it as compatibility/reference evidence for classic verbs/functions
- move long-term authority to source contracts + `SYSFUNC`/compat metadata
- generate it later

## Promotion Rules

None of the following should be promoted automatically:

- HELP rows
- manualgen pages
- selfdoc reports
- generated command pages
- hand-edited `dotref.hpp` or `foxref.hpp`
- hand-edited `helpdata_messages.cpp`

Promotion to default authority requires explicit confirmation that:

1. source implementation agrees
2. metadata row exists and is aligned
3. runtime proof exists where relevant
4. generated/publication layers are downstream of that truth

## Practical Next Steps

1. Treat `SYSMSG` as the canonical identity lane for messages.
2. Treat `SYSCMD`/`SYSSUBCMD`/`SYSFUNC`/`SYSARGS` as the canonical metadata
   lanes for command/function identity and arguments.
3. Keep `helpdata_messages.*`, `dotref.hpp`, and `foxref.hpp` compiled for now.
4. Build generators so those compiled files become artifacts, not primary
   authoring homes.
5. Keep HELP, selfdoc, metacollect, and manualgen downstream of source plus
   metadata truth.

## One-Sentence Summary

Source remains implementation authority, metadata becomes canonical authoring
authority, compiled headers/catalogs remain generated runtime fallbacks, and
HELP/SelfDoc/manualgen remain evidence and publication layers downstream of
that truth.

## Related Implementation Backlog

Execution order, seeding order, generator phases, and acceptance checks are
tracked in:

- [help_message_reference_implementation_backlog_v1.md](/D:/code/ccode/dottalkpp/docs/authority/help_message_reference_implementation_backlog_v1.md)
