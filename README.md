# DotTalk++ / x64base

**A working educational xBase / FoxPro-inspired database runtime, command shell, and architecture lab built in modern C++.**

---

## Overview

DotTalk++ is a modern C++ xBase-inspired database runtime, command shell, teaching system, and architecture lab.

It is not presented as a finished commercial database product.

It is a working educational and research system: part DBF database runtime, part command shell, part historical teaching environment, part metadata experiment, and part architecture laboratory.

The project draws inspiration from the classic xBase lineage:

```text
dBase   - early interactive database shell
Clipper - compiled xBase systems
FoxPro  - relational navigation and index-driven querying
```

DotTalk++ preserves many useful ideas from those systems while extending them with modern C++ structure, help catalogs, relational traversal, tuple projection, scripting, automation, metadata tables, validation tools, browsers, and a simple text user interface.

It is not a direct port of an older product.

It is a broader reimplementation and expansion.

DotTalk++ sits between FoxPro and Clipper:

```text
interactive and stateful like FoxPro
extensible and compilable like Clipper
```

The project is intended to serve as:

```text
a working DBF database runtime
a relational exploration environment
a scripting and automation shell
a teaching system for database concepts
an architecture lab for metadata, HELP, validation, and browser design
```

A major design goal is for DotTalk++ to become increasingly self-documenting.

Commands, functions, arguments, aliases, subcommands, metadata tables, HELP output, validation reports, scripts, browsers, and simple TUI surfaces are being designed to reinforce each other instead of living as separate hand-written descriptions.

Some subsystems are already runtime-proven. Other subsystems are still canaries or integration work. The repository is intentionally honest about that distinction.

The goal is to build finished educational tools, database utilities, and applications from proven layers, not to pretend every subsystem is complete at the same time.

---

## History

DotTalk++ traces back to 1993, when Derald Grimwood wrote a small ANSI C database program as a practical and experimental system.

That early program included fixed-length record storage and a simple in-memory B-tree.

In 2025, the earlier work was revived and used as the conceptual basis for a modern 64-bit rebuild in C++.

The result became DotTalk++: not a direct port, but a broader reimplementation and expansion.

The project honors the xBase tradition while extending it into a modern, teachable, experiment-friendly database runtime.

Part of the project’s educational value is historical. DotTalk++ shows students a transitional period in computing: the 8-bit / early-16-bit personal-computer era of the 8088, 8086, DOS, text UIs, command systems, DBF files, and direct file-based data work.

This is not nostalgia for its own sake.

It is a way to make the layers visible.

---

## Educational Purpose

DotTalk++ is built for learning as much as for execution.

The system is intended to help students see concepts that are usually hidden:

```text
table files
records
fields
field types
work areas
indexes
index tags
relations
tuple traversal
schemas
metadata
HELP generation
runtime validation
simple text interfaces
command discovery
```

Instead of presenting the database as a black box, DotTalk++ exposes the moving parts.

A student can open a table, inspect its structure, browse records, change order, see relation trees, follow child records, inspect metadata tables, use HELP, run validation checks, and compare command documentation against runtime reflection.

The goal is not to teach old software as a museum piece.

The goal is to use an understandable historical model to explain modern ideas:

```text
classic DBF tables        -> structured storage
records and fields        -> physical data modeling
indexes                   -> access paths
work areas                -> runtime context
relations                 -> graph navigation
tuple grids               -> joined views
metadata tables           -> self-description
HELP and CMDHELPCHK       -> documentation as executable contract
simple TUI menus          -> command discovery and reinforcement
scripts                   -> repeatable workflows
```

DotTalk++ uses that visible, command-centered period of personal computing as a teaching surface for modern database ideas.

---

## Design Philosophy

DotTalk++ is built around a few practical beliefs:

* Preserve the engineering behavior of FoxPro/xBase where it still makes sense
* Avoid copying branding or unnecessary legacy constraints
* Separate engine, interface, metadata, HELP, validation, and storage concerns
* Keep the command surface understandable
* Let runtime behavior prove architecture
* Teach by exposing the layers: records, fields, indexes, relations, work areas, metadata, HELP, and validation
* Use the command surface as a learning tool, not just an operator interface
* Treat the simple TUI as reinforcement for command discovery and historical context
* Show students how personal computing moved from files and commands toward modern database and application systems
* Design toward a self-documenting runtime: commands, functions, metadata, HELP, reports, browsers, and validators should agree
* Build gradually from:

  * CLI experimentation
  * → scripts and repeatable smoke tests
  * → simple TUI reinforcement
  * → relation-aware browsing
  * → metadata-driven HELP
  * → runtime validation
  * → Python integration
  * → future teaching applications and utilities

A useful project rule:

```text
Conventions suggest.
Registration declares.
Metadata records.
Runtime proves.
Validators enforce.
```

DotTalk++ is intentionally stateful and interactive.

It exposes important runtime concepts directly:

```text
current work area
current record pointer
active order/index
active filter
relation graph
buffering state
workspace state
```

The goal is to make database behavior visible and understandable during live operation, rather than hiding it behind abstraction.

---

## Working Model

DotTalk++ can be understood as four cooperating layers:

```text
1. Command Layer
   interactive commands, scripts, command discovery, and automation

2. Data Layer
   tables, records, fields, work areas, indexes, and storage behavior

3. Logic Layer
   expressions, predicates, functions, validation, and control flow

4. Projection Layer
   LIST, SMARTLIST, TUPLE, REL ENUM, ERSATZ, SMARTBROWSE, SIMPLEBROWSE, and other browsers
```

This model is useful for students because it separates:

```text
what the user types
what the data engine stores
how logic is evaluated
how results are projected back to the screen
```

---

## Current Status

**Project:** Working beta / active development  
**Engine:** Working beta  
**Indexing (INX/CNX/CDX/LMDB):** Active  
**Memo System:** Active, with canaries  
**CLI / DotScript:** Active and usable  
**Tuple / Relations / Browsers:** Active; asymmetric relation persistence, ERSATZ relational browsing, SMARTBROWSE/ARTBROWSE record browsing, and SIMPLEBROWSE tuple browsing are runtime-proven  
**HELP / Metadata:** Active; reflection-backed HELP exists, SYS* congruence validation is next  
**DDL:** Active / partial  
**DrawIO:** Helper implemented; metadata-generated diagrams planned  
**Python Binding:** Active, with read-only smoke coverage  
**Simple TUI:** Active / experimental  

Recent verified checkpoint:

```text
3176203 Add asymmetric REL persistence for metadata graph
```

Verified in the current development cycle:

```text
clean rebuild: PASS
metadata_rel workspace open DBF CDX: PASS
asymmetric REL ADD: PASS
workspace save/load asymmetric relations: PASS
x32 MCC legacy relation restore: PASS
ERSATZ relational browser: PASS
ERSATZ tuple grid: PASS
SMARTBROWSE / ARTBROWSE smoke: PASS
SIMPLEBROWSE / SB tuple listing smoke: PASS
simple TUI menu surface: visible and active
```

Some parts are runtime-proven. Other parts are canaries or integration work. The project deliberately separates those categories so that finished tools can be built on proven layers.

---

## Core Engine

DotTalk++ includes a DBF-style table engine inspired by classic xBase systems.

Current engine work includes:

* DBF-style table handling
* Multiple table flavors, including x32 and x64-family work
* Field-level validation and type support
* Cursor-based navigation model
* Work areas, selection, record movement, and table inspection
* Separation between table behavior, memo payloads, indexes, command surface, metadata, and UI

DbArea remains the primary runtime owner of records, cursor state, mutation behavior, and table flavor behavior.

This boundary matters because the project is trying to avoid mixing storage, navigation, metadata, UI, HELP, validation, and command responsibilities into one accidental layer.

---

## Table Flavors and x64 Work

DotTalk++ works with older-style DBF data while also exploring extended x64 table formats.

The x64 direction is not just “bigger DBF.” It is also about better metadata, cleaner structure, wider headers, modernized table descriptions, and stronger runtime interpretation.

Current x64-family work includes:

* x64 table/header experiments
* metadata table support
* schema and sidecar work
* CDX/LMDB-backed index experiments
* runtime kind and table flavor reporting

Status: active. Some x64 behaviors are proven, while others remain canaries.

---

## Indexing System

DotTalk++ supports several indexing models:

| Type | Purpose | Status |
| ---- | ------- | ------ |
| INX | Legacy/simple index | Active / stable |
| CNX | Transitional multi-tag | Active / stable |
| CDX | Logical multi-tag surface | Active development |
| LMDB | Physical backend | Active development |

### CDX + LMDB Architecture

```text
INDEXES/
  students.cdx        <- container / logical surface

LMDB/
  students.cdx.d/     <- physical backend
```

* CDX is the user-facing logical container
* LMDB is the physical persistence backend
* Ordinary command-surface language should talk about CDX, not LMDB internals
* `BUILDLMDB` materializes index data from CDX metadata

This area is active. Some index reporting and mutation paths are still canaries.

The intended architecture is:

```text
CDX  = logical multi-tag abstraction
LMDB = physical backend hidden behind CDX
```

That distinction is important because students and users should learn the index concept before being forced into backend implementation details.

---

## Navigation Model

DotTalk++ preserves many classic command-oriented navigation ideas:

```text
SET ORDER TO TAG <name>
TOP
BOTTOM
SKIP
SEEK <value>
GOTO <n>
```

The runtime tracks physical and logical record movement, and the project is moving toward shared iterator behavior across LIST, SMARTLIST, browsers, relation traversal, and tuple output.

SMARTLIST is intended to become the primary table-aware listing surface for non-interactive output.

---

## Relations, Browsers, and Tuple Traversal

DotTalk++ has a relation-aware workspace model.

Legacy same-field relations remain supported:

```text
REL ADD STUDENTS ENROLL ON SID
```

Recent work added asymmetric relation support:

```text
REL ADD SYSCMD SYSSUBCMD ON CAN_NAME TO PARENT
REL ADD SYSSUBCMD SYSENTVAR ON QUAL_NAME TO HELP_OWNR
```

This allows metadata tables to remain properly normalized instead of being reshaped to fit same-field-only joins.

The following metadata graph is now runtime-proven:

```text
SYSCMD.CAN_NAME      -> SYSSUBCMD.PARENT
SYSSUBCMD.QUAL_NAME  -> SYSENTVAR.HELP_OWNR
```

The graph also survives workspace persistence:

```text
WORKSPACE SAVE metadata_rel
WORKSPACE CLOSE
WORKSPACE LOAD metadata_rel
```

The browser layer is where relation work becomes visible. ERSATZ shows relation trees and tuple grids, SMARTBROWSE/ARTBROWSE provides interactive record browsing, and SIMPLEBROWSE/SB gives quick tuple-style inspection.

The x32 MCC sample workspace restores legacy same-field relations and exercises the browser stack successfully.

---

## Workspace System

Workspaces can restore groups of open areas and relations.

Current proven examples include:

```text
do x32
ersatz mcc
```

which restores the MCC sample workspace, and:

```text
do metadata
workspace load metadata_rel
```

which restores the x64 metadata workspace with asymmetric relations.

Recent verified behavior:

```text
WORKSPACE LOAD: restored 8 area(s) and 2 relation(s).
WORKSPACE LOAD: restored 12 area(s) and 15 relation(s).
```

Workspaces matter because DotTalk++ is not only about opening one file. It is about preserving a live context: areas, aliases, relations, paths, orders, and eventually richer metadata.

---

## CLI and DotScript

Interactive shell:

```text
DotTalk++ type HELP. USE, SELECT <n>, AREA, COLOR, ABOUT, QUIT
```

DotScript supports:

* Batch execution
* Runtime smoke scripts
* Canary scripts
* Reusable setup scripts such as `do x32` and `do metadata`
* Educational and diagnostic workflows

The command surface is part of the design, not just a test harness.

Students can type commands, run scripts, browse records, inspect areas, and see the system respond directly.

---

## Simple TUI

DotTalk++ includes a simple Turbo Vision-style text user interface.

The TUI is student-facing. It is meant to reinforce the command system, not replace it. Menus expose the same underlying commands students can type directly, helping them connect command language, workspace state, table browsing, and system behavior.

The TUI also gives historical context. It reflects the style of software from the 8088 / 8086 personal-computer era, when text interfaces, keyboard navigation, menus, records, and command prompts were normal parts of daily computing.

Current TUI work includes:

* Top-level menu bar
* Command window
* Output window
* Basic workspace/status panels
* Menu access to command groups such as workspace, table, record, index, lists, browse, relations, tuples, functions, commands, windows, and help
* Keyboard shortcuts and command-line integration

Example menu groups:

```text
Sys
File
Work
Erz
Table
Record
Index
Lists
Browse
Rel
Tuple
Funcs
Cmd
Window
Help
```

Status: active / experimental. The CLI remains the canonical runtime surface; the TUI is a convenience, discovery, and teaching layer.

The TUI is intentionally simple. It is not meant to be a polished IDE. It is meant to make the command system easier to discover and easier to teach.

---

## Metadata and Self-Documentation

DotTalk++ is being designed to become a self-documenting system.

That does not mean every document is automatically generated today. It means the runtime is being shaped so that commands, functions, arguments, aliases, subcommands, metadata tables, HELP output, reports, scripts, browsers, and validators can increasingly describe and check each other.

The intended path is:

```text
runtime truth
  -> ReferenceCollection / reflection model
  -> x64 metadata catalog tables
  -> CDX logical indexes backed by LMDB
  -> HELP / CMDHELP / reports
  -> validators such as CMDHELPCHK
```

Current reality:

* `ReferenceCollection` exists
* Runtime reflection includes commands, subcommands, entry variants, functions, and messages
* HELP can use reflected command, subcommand, and function information
* CMDHELPCHK can audit reflection data
* SYS* metadata tables exist and open as a workspace
* Asymmetric relations now connect key metadata tables

Next step:

```text
CMDHELPCHK / SYS* congruence validation
```

That means checking whether runtime reflection, generated HELP, metadata catalog tables, scripts, reports, and browser surfaces agree.

The long-term goal is documentation that is not merely written by hand, but backed by the running system.

---

## HELP System

The HELP system is active and mixed-source.

It currently draws from:

* Runtime reflection / `ReferenceCollection`
* Command documentation catalogs
* Expression function documentation
* FoxPro compatibility references
* DotTalk-native references
* Educational/system references
* Legacy HELP data paths

Examples:

```text
HELP
HELP GIANT
HELP BETA
HELP FUNCTION <name>
HELP FUNCTIONS
HELP PREDICATES
HELP SQL
HELP PS
HELP /FOX <topic>
HELP /DOT <topic>
HELP /ED <topic>
HELP <command>
```

Reflection-backed HELP exists. Full SYS* metadata-driven HELP rendering is still an integration target.

For students, HELP is not only a reference manual. It is part of the teaching loop:

```text
type a command
ask for HELP
inspect metadata
validate reflection
compare runtime behavior
```

---

## CMDHELPCHK

`CMDHELPCHK` is the current validation tool for documentation/runtime congruence.

It supports reflection audit mode:

```text
CMDHELPCHK
CMDHELPCHK REF
CMDHELPCHK REFLECT
```

and legacy HELP DBF validation mode:

```text
CMDHELPCHK <help-output-directory>
```

Current reflection checks include:

```text
unresolved entry variants
duplicate canonical commands
duplicate subcommands
missing parent commands
duplicate functions
invalid function argument ranges
missing function categories
```

Status: active. The next milestone is comparing runtime reflection against the x64 SYS* metadata catalog.

This is one of the places where DotTalk++ tries to turn documentation into an executable contract.

---

## DDL and Schema Tools

DotTalk++ includes an active DDL command surface.

Current DDL capabilities include:

```text
DDL FETCH <url> TO <file>
DDL VALIDATE <schema.json> USING <validator.json>
DDL CREATE DBF <output.dbf> FROM <schema.json>
```

The DDL path can create DBF structures from JSON schema definitions and emit sidecar metadata files such as:

```text
<table>.ddl.json
<table>.load.json
<table>.indexes.json
<table>.schema.copy.json
```

Status: active / partial.

DBF creation and blank seeding exist. CSV seeding is not complete yet and should not be treated as a finished import pipeline.

Educationally, DDL is useful because it connects a visible table file to a schema document. A student can see that a DBF is not magic: it has fields, types, lengths, structure, and metadata that can be generated and inspected.

---

## DrawIO / Design Surface

DotTalk++ includes a small `DRAWIO` helper command:

```text
DRAWIO
DRAWIO OPEN
DRAWIO OPEN <url>
```

Current behavior opens diagrams.net / draw.io in the default browser.

Future direction: generate useful diagrams from DotTalk++ metadata, relations, schemas, and runtime catalogs.

Current status: helper implemented; metadata-generated diagrams are planned, not complete.

This is a good example of the project’s general approach: start with a small useful command, then connect it later to metadata, schemas, and relation graphs.

---

## Memo System

Object-oriented design direction:

```text
DbArea -> MemoRef -> MemoManager -> MemoObject -> MemoStore
```

Goals and partial capabilities:

* Multi-record memo isolation
* Persistence across sessions
* Safer PACK behavior
* Future-ready large-object handling

Status: active, but still treated with canaries. Some memo payload/backend attachment paths need more proof before being called complete.

Memo is intentionally separated from the core table engine. That separation is part of the architecture, because table records and large object payloads should not be treated as the same concern.

---

## Expression Engine

Supports:

* Numeric functions
* String functions
* Date functions
* FoxPro-style expression behavior
* Runtime evaluation
* Function documentation integration

Example:

```text
CALC SOUNDEX("WHITE")
-> W300
```

Expression functions are increasingly tied into HELP and reflection.

This matters for students because expressions connect data inspection, filtering, calculation, and command behavior.

---

## Python Binding

`pydottalk` is an optional Python binding.

Current status:

* Builds in the Windows development environment
* Can import under Python 3.12
* Has basic read-only DBF smoke coverage

This is active integration work, not yet a full public API promise.

The educational value is that the same table concepts can eventually be seen from both the DotTalk++ command surface and Python.

---

## Runtime Scripts and Canaries

DotTalk++ includes runtime scripts for smoke testing, setup, and canary checks.

Examples include scripts that:

* Set x32 paths
* Set x64 metadata paths
* Open workspace estates
* Run non-destructive smoke tests
* Exercise HELP and command surfaces
* Exercise relation and browser behavior

Canaries are intentionally part of the workflow. They help distinguish:

```text
implemented and proven
implemented but fragile
designed but not complete
legacy behavior preserved for compatibility
```

---

## Feature Status Matrix

| Area | Status | Notes |
| ---- | ------ | ----- |
| DBF / xBase table engine | Active | Core table, cursor, record, and structure behavior exist. |
| x32 DBF runtime | Proven | MCC sample workspace restores and browses successfully. |
| x64 DBF / metadata work | Active | x64 metadata tables can be opened with CDX/LMDB attached. |
| INX / CNX / CDX indexing | Active | INX/CNX are established; CDX is the logical multi-tag surface with LMDB backend work. |
| LMDB backend | Active | Used behind CDX for x64-family indexing. |
| Relations | Recently advanced | Same-field relations and asymmetric `ON parent TO child` relations are both supported. |
| Workspace persistence | Proven for relation graph | Asymmetric relations now survive `WORKSPACE SAVE` / `WORKSPACE LOAD`. |
| Browsers | Active / runtime-proven | ERSATZ relational browser, SMARTBROWSE/ARTBROWSE record browser, and SIMPLEBROWSE/SB tuple browser exist and have current smoke evidence. |
| Tuple traversal | Active | ERSATZ and relation-aware tuple grids are runtime-proven for MCC sample data. |
| DDL | Active / partial | JSON-schema DBF creation and sidecar metadata exist; CSV seeding remains incomplete. |
| HELP | Active / mixed-source | Uses reflection, catalogs, function docs, and legacy references. |
| CMDHELPCHK | Active | Reflection audit and legacy HELP DBF validation exist. SYS* congruence validation is next. |
| Metadata self-documentation | Active / emerging | Runtime reflection exists; SYS* catalog alignment is the next focus. |
| DrawIO | Helper implemented / generation planned | Command opens diagrams.net; metadata-generated diagrams are not yet complete. |
| Memo | Active / canary | OO memo architecture exists; some payload/backend attachment paths still need proof. |
| Python binding | Active | `pydottalk` builds and has basic read-only smoke coverage. |
| Simple TUI | Active / experimental | Turbo Vision-style text UI exposes runtime command groups through menus, command window, output window, and workspace/status panels; used as a learning and command-discovery layer. |

---

## Command Highlights

### Table Operations

```text
USE <table>
SELECT <n>
SELECT <alias>
AREA
DBAREA
DBAREAS
STRUCT
```

### Indexing

```text
SET INDEX TO students.cdx
SET ORDER TO TAG lname
BUILDLMDB
REINDEX
```

### Navigation

```text
TOP
BOTTOM
SKIP
SEEK <value>
GOTO <n>
```

### Query / Display

```text
SMARTLIST
LIST
COUNT FOR <expr>
SCAN / ENDSCAN
LOCATE FOR <expr>
```

### Browsing

```text
SMARTBROWSE
ARTBROWSE
SIMPLEBROWSE
SB
ERSATZ
ERSATZ MCC
ERSATZ LOAD <name>
```

### Relations

```text
REL ADD STUDENTS ENROLL ON SID
REL ADD SYSCMD SYSSUBCMD ON CAN_NAME TO PARENT
REL LIST ALL
REL ENUM
```

### Workspace

```text
WORKSPACE OPEN DBF
WORKSPACE OPEN DBF CDX
WORKSPACE SAVE <name>
WORKSPACE LOAD <name>
WORKSPACE CLOSE
WSREPORT
```

### Metadata

```text
do metadata
workspace open dbf cdx
workspace load metadata_rel
```

### HELP / Validation

```text
HELP
HELP <command>
HELP FUNCTION <name>
CMDHELPCHK
CMDHELPCHK REF
```

### DDL

```text
DDL FETCH <url> TO <file>
DDL VALIDATE <schema.json> USING <validator.json>
DDL CREATE DBF <output.dbf> FROM <schema.json>
```

### DrawIO

```text
DRAWIO
DRAWIO OPEN
DRAWIO OPEN <url>
```

---

## Listing and Browsing Surfaces

DotTalk++ has both listing tools and browser tools. They overlap, but they are not the same thing.

* **LIST**

  * Developer-oriented table printer
  * Useful for low-level inspection and compatibility testing
  * Cursor-driven

* **SMARTLIST**

  * Table-aware listing surface
  * Order-aware
  * Expression-driven
  * Intended future primary listing interface for non-interactive table output

* **SIMPLEBROWSE / SB**

  * Read-only workspace browser
  * Tuple-style output
  * Useful for fast inspection of current area/workspace state

* **SMARTBROWSE / ARTBROWSE**

  * Interactive record browser
  * Supports navigation, filtering, order switching, schema display, JSON display, and relation-aware child exploration
  * Active beta surface

* **ERSATZ**

  * Relation-aware browser/workspace launcher
  * Useful for proving relation trees, descendant summaries, and tuple grids
  * Current primary proof surface for relation-aware browsing

* **Simple TUI**

  * Text-mode menu layer
  * Provides menu-driven command discovery
  * Wraps many CLI/runtime commands without replacing them
  * Active beta surface for workspace, table, browse, relation, tuple, command, and help workflows

The browser layer is important because DotTalk++ is not only a command engine. It is also an inspection environment.

---

## Index Lifecycle

```text
CDX CREATE
SET INDEX
SET ORDER
BUILDLMDB
-> LMDB backend ready
```

Mutation model:

* Append / Replace -> active work
* Delete / Recall -> still needs complete proof
* Buffered vs direct write modes planned
* Reporting surfaces may lag actual index state in some canary cases

---

## Current Work Focus

The current useful work is validation and congruence, not broad feature expansion.

Primary focus:

* CMDHELPCHK v2
* HELP / SYS* congruence checks
* Metadata catalog reports
* Proof that reflected commands, generated HELP, and SYS* tables agree

Secondary active areas:

* CDX / LMDB lifecycle cleanup
* SMARTLIST improvement
* Memo payload/backend proof
* DDL seeding and schema workflow expansion
* Metadata-generated DrawIO diagrams
* Continued TUI cleanup and command-discovery reinforcement
* Browser polish without breaking command semantics

---

## Architecture Overview

```text
xbase/          <- core table engine
xindex/         <- indexing systems
memo/           <- memo subsystem
xexpr/          <- expression engine
cli/            <- command interface, workspace commands, browsers, HELP, DDL, DrawIO helpers
help/           <- reflection and HELP model
tuple/          <- tuple / row / cell / relation-aware adapters
pydottalk/      <- Python bindings
tv/             <- simple TUI components
dottalkpp/      <- runtime data, scripts, workspaces, tests, help
```

---

## Design Rules

* DbArea is the runtime truth for records, cursor, mutation, and table flavor behavior
* Memo payload is external to table engine
* CDX is the logical multi-tag index abstraction
* LMDB is the physical backend, hidden behind normal command-surface wording
* HELP should increasingly be generated or validated from runtime truth
* DotScript is canonical for automation
* Python is a future integration surface
* Tuple infrastructure is relation-aware and orthogonal to raw table storage
* Browsers are first-class inspection surfaces, not just formatted LIST output
* The TUI is a convenience and discovery layer; the command language remains canonical
* Student learning matters: visible layers are a feature, not a flaw

---

## Example Sessions

### x32 MCC relation smoke

```text
do x32
ersatz mcc
ersatz
```

Expected behavior:

```text
WORKSPACE LOAD: restored 12 area(s) and 15 relation(s).
ROWS SHOWN: ... | STATUS: OK
```

### Browser smoke

```text
do x32
ersatz load mcc
ersatz
select students
smartbrowse
simplebrowse
```

Expected behavior:

```text
ERSATZ Relational Browser opens on STUDENTS.
SMARTBROWSE / ARTBROWSE shows interactive record browsing state.
SIMPLEBROWSE emits tuple-style rows from the selected area.
```

### x64 metadata relation smoke

```text
do metadata
workspace open dbf cdx
rel add syscmd syssubcmd on can_name to parent
rel add syssubcmd sysentvar on qual_name to help_ownr
select 1
rel list all
```

Expected relation shape:

```text
SYSCMD
  -> SYSSUBCMD ON can_name TO parent
    -> SYSENTVAR ON qual_name TO help_ownr
```

### x64 metadata relation persistence

```text
workspace save metadata_rel
workspace close
do metadata
workspace load metadata_rel
select 1
rel list all
select 7
rel list all
```

Expected behavior:

```text
WORKSPACE LOAD: restored 8 area(s) and 2 relation(s).
```

### HELP / reflection smoke

```text
help
help functions
help function soundex
cmdhelpchk
cmdhelpchk ref
```

Expected behavior:

```text
HELP displays mixed-source command/function help.
CMDHELPCHK reflection mode reports command, subcommand, and function checks.
```

---

## Roadmap

### Short Term

* CMDHELPCHK / SYS* congruence validation
* HELP metadata alignment
* Preserve asymmetric relation behavior while building reports on top of it
* Continue CDX / LMDB lifecycle cleanup
* Keep x32 MCC regression smoke passing
* Keep browser smoke paths passing
* Keep the simple TUI aligned with real command names

### Mid Term

* Stronger metadata reports
* Generated HELP validation
* SMARTLIST improvements
* Tuple engine stabilization
* Memo backend proof
* DDL seeding improvements
* Browser polish
* Metadata-aware TUI help and command discovery

### Long Term

* Metadata-generated diagrams
* Stronger Python integration
* Service layer experiments
* UI expansion
* Migration and teaching tools
* Better educational labs around tables, indexes, relations, metadata, and HELP validation
* Finished educational tools, database utilities, and applications built on the proven runtime

---

## Naming and Identity

DotTalk++ preserves the spirit of FoxPro/xBase engineering without copying legacy branding.

It values:

* Direct command interaction
* Understandable table files
* Fast inspection
* Scriptable workflows
* Relation-aware browsing
* Self-documenting runtime metadata
* Learning through visible system behavior

The project is not trying to pretend the past was perfect. It is trying to recover the parts that were teachable, direct, and powerful.

---

## Why This Exists

DotTalk++ exists to make database systems understandable again.

It is not trying to be a commercial database product. It is a working educational and research system built around ideas that are still worth teaching:

* records and fields
* table files
* indexes and access paths
* work areas and runtime state
* relations and graph traversal
* commands and scripts
* HELP as part of the system
* metadata as self-description
* HELP and validation as proof

The project draws from xBase, dBase, Clipper, FoxPro, DOS-era command systems, and early personal-computer software because those systems made many of the layers visible.

Modern software often hides those layers.

DotTalk++ tries to expose them again, but with cleaner modern architecture underneath.

Some areas are still beta because they are being proven layer by layer. The goal is to finish useful educational tools, database utilities, and applications from the pieces that prove themselves.

---

## Author

Derald Grimwood  
B.S. Management Information Systems  
xBase / SAP / ERP background

---

## License

(To be defined)

---

## Final Notes

> User interfaces change, languages change, but the underlying database principles remain constant.
>
> — Derald Grimwood

> Preserve the past. Teach the layers. Fix the architecture. Move forward.compare runtime behavior
```

---

## CMDHELPCHK

`CMDHELPCHK` is the current validation tool for documentation/runtime congruence.

It supports reflection audit mode:

```text
CMDHELPCHK
CMDHELPCHK REF
CMDHELPCHK REFLECT
```

and legacy HELP DBF validation mode:

```text
CMDHELPCHK <help-output-directory>
```

Current reflection checks include:

```text
unresolved entry variants
duplicate canonical commands
duplicate subcommands
missing parent commands
duplicate functions
invalid function argument ranges
missing function categories
```

Status: active. The next milestone is comparing runtime reflection against the x64 SYS* metadata catalog.

This is one of the places where DotTalk++ tries to turn documentation into an executable contract.

---

## DDL and Schema Tools

DotTalk++ includes an active DDL command surface.

Current DDL capabilities include:

```text
DDL FETCH <url> TO <file>
DDL VALIDATE <schema.json> USING <validator.json>
DDL CREATE DBF <output.dbf> FROM <schema.json>
```

The DDL path can create DBF structures from JSON schema definitions and emit sidecar metadata files such as:

```text
<table>.ddl.json
<table>.load.json
<table>.indexes.json
<table>.schema.copy.json
```

Status: active / partial.

DBF creation and blank seeding exist. CSV seeding is not complete yet and should not be treated as a finished import pipeline.

Educationally, DDL is useful because it connects a visible table file to a schema document. A student can see that a DBF is not magic: it has fields, types, lengths, structure, and metadata that can be generated and inspected.

---

## DrawIO / Design Surface

DotTalk++ includes a small `DRAWIO` helper command:

```text
DRAWIO
DRAWIO OPEN
DRAWIO OPEN <url>
```

Current behavior opens diagrams.net / draw.io in the default browser.

Future direction: generate useful diagrams from DotTalk++ metadata, relations, schemas, and runtime catalogs.

Current status: helper implemented; metadata-generated diagrams are planned, not complete.

This is a good example of the project’s general approach: start with a small useful command, then connect it later to metadata, schemas, and relation graphs.

---

## Memo System

Object-oriented design direction:

```text
DbArea -> MemoRef -> MemoManager -> MemoObject -> MemoStore
```

Goals and partial capabilities:

* Multi-record memo isolation
* Persistence across sessions
* Safer PACK behavior
* Future-ready large-object handling

Status: active, but still treated with canaries. Some memo payload/backend attachment paths need more proof before being called complete.

Memo is intentionally separated from the core table engine. That separation is part of the architecture, because table records and large object payloads should not be treated as the same concern.

---

## Expression Engine

Supports:

* Numeric functions
* String functions
* Date functions
* FoxPro-style expression behavior
* Runtime evaluation
* Function documentation integration

Example:

```text
CALC SOUNDEX("WHITE")
-> W300
```

Expression functions are increasingly tied into HELP and reflection.

This matters for students because expressions connect data inspection, filtering, calculation, and command behavior.

---

## Python Binding

`pydottalk` is an optional Python binding.

Current status:

* Builds in the Windows development environment
* Can import under Python 3.12
* Has basic read-only DBF smoke coverage

This is active integration work, not yet a full public API promise.

The educational value is that the same table concepts can eventually be seen from both the DotTalk++ command surface and Python.

---

## Runtime Scripts and Canaries

DotTalk++ includes runtime scripts for smoke testing, setup, and canary checks.

Examples include scripts that:

* Set x32 paths
* Set x64 metadata paths
* Open workspace estates
* Run non-destructive smoke tests
* Exercise HELP and command surfaces
* Exercise relation and browser behavior

Canaries are intentionally part of the workflow. They help distinguish:

```text
implemented and proven
implemented but fragile
designed but not complete
legacy behavior preserved for compatibility
```

---

## Feature Status Matrix

| Area | Status | Notes |
| ---- | ------ | ----- |
| DBF / xBase table engine | Active | Core table, cursor, record, and structure behavior exist. |
| x32 DBF runtime | Proven | MCC sample workspace restores and browses successfully. |
| x64 DBF / metadata work | Active | x64 metadata tables can be opened with CDX/LMDB attached. |
| INX / CNX / CDX indexing | Active | INX/CNX are established; CDX is the logical multi-tag surface with LMDB backend work. |
| LMDB backend | Active | Used behind CDX for x64-family indexing. |
| Relations | Recently advanced | Same-field relations and asymmetric `ON parent TO child` relations are both supported. |
| Workspace persistence | Proven for relation graph | Asymmetric relations now survive `WORKSPACE SAVE` / `WORKSPACE LOAD`. |
| Browsers | Active / runtime-proven | ERSATZ relational browser, SMARTBROWSE/ARTBROWSE record browser, and SIMPLEBROWSE/SB tuple browser exist and have current smoke evidence. |
| Tuple traversal | Active | ERSATZ and relation-aware tuple grids are runtime-proven for MCC sample data. |
| DDL | Active / partial | JSON-schema DBF creation and sidecar metadata exist; CSV seeding remains incomplete. |
| HELP | Active / mixed-source | Uses reflection, catalogs, function docs, and legacy references. |
| CMDHELPCHK | Active | Reflection audit and legacy HELP DBF validation exist. SYS* congruence validation is next. |
| Metadata self-documentation | Active / emerging | Runtime reflection exists; SYS* catalog alignment is the next focus. |
| DrawIO | Helper implemented / generation planned | Command opens diagrams.net; metadata-generated diagrams are not yet complete. |
| Memo | Active / canary | OO memo architecture exists; some payload/backend attachment paths still need proof. |
| Python binding | Active | `pydottalk` builds and has basic read-only smoke coverage. |
| Simple TUI | Active / experimental | Turbo Vision-style text UI exposes runtime command groups through menus, command window, output window, and workspace/status panels; used as a learning and command-discovery layer. |

---

## Command Highlights

### Table Operations

```text
USE <table>
SELECT <n>
SELECT <alias>
AREA
DBAREA
DBAREAS
STRUCT
```

### Indexing

```text
SET INDEX TO students.cdx
SET ORDER TO TAG lname
BUILDLMDB
REINDEX
```

### Navigation

```text
TOP
BOTTOM
SKIP
SEEK <value>
GOTO <n>
```

### Query / Display

```text
SMARTLIST
LIST
COUNT FOR <expr>
SCAN / ENDSCAN
LOCATE FOR <expr>
```

### Browsing

```text
SMARTBROWSE
ARTBROWSE
SIMPLEBROWSE
SB
ERSATZ
ERSATZ MCC
ERSATZ LOAD <name>
```

### Relations

```text
REL ADD STUDENTS ENROLL ON SID
REL ADD SYSCMD SYSSUBCMD ON CAN_NAME TO PARENT
REL LIST ALL
REL ENUM
```

### Workspace

```text
WORKSPACE OPEN DBF
WORKSPACE OPEN DBF CDX
WORKSPACE SAVE <name>
WORKSPACE LOAD <name>
WORKSPACE CLOSE
WSREPORT
```

### Metadata

```text
do metadata
workspace open dbf cdx
workspace load metadata_rel
```

### HELP / Validation

```text
HELP
HELP <command>
HELP FUNCTION <name>
CMDHELPCHK
CMDHELPCHK REF
```

### DDL

```text
DDL FETCH <url> TO <file>
DDL VALIDATE <schema.json> USING <validator.json>
DDL CREATE DBF <output.dbf> FROM <schema.json>
```

### DrawIO

```text
DRAWIO
DRAWIO OPEN
DRAWIO OPEN <url>
```

---

## Listing and Browsing Surfaces

DotTalk++ has both listing tools and browser tools. They overlap, but they are not the same thing.

* **LIST**

  * Developer-oriented table printer
  * Useful for low-level inspection and compatibility testing
  * Cursor-driven

* **SMARTLIST**

  * Table-aware listing surface
  * Order-aware
  * Expression-driven
  * Intended future primary listing interface for non-interactive table output

* **SIMPLEBROWSE / SB**

  * Read-only workspace browser
  * Tuple-style output
  * Useful for fast inspection of current area/workspace state

* **SMARTBROWSE / ARTBROWSE**

  * Interactive record browser
  * Supports navigation, filtering, order switching, schema display, JSON display, and relation-aware child exploration
  * Active beta surface

* **ERSATZ**

  * Relation-aware browser/workspace launcher
  * Useful for proving relation trees, descendant summaries, and tuple grids
  * Current primary proof surface for relation-aware browsing

* **Simple TUI**

  * Text-mode menu layer
  * Provides menu-driven command discovery
  * Wraps many CLI/runtime commands without replacing them
  * Active beta surface for workspace, table, browse, relation, tuple, command, and help workflows

The browser layer is important because DotTalk++ is not only a command engine. It is also an inspection environment.

---

## Index Lifecycle

```text
CDX CREATE
SET INDEX
SET ORDER
BUILDLMDB
-> LMDB backend ready
```

Mutation model:

* Append / Replace -> active work
* Delete / Recall -> still needs complete proof
* Buffered vs direct write modes planned
* Reporting surfaces may lag actual index state in some canary cases

---

## Current Work Focus

The current useful work is validation and congruence, not broad feature expansion.

Primary focus:

* CMDHELPCHK v2
* HELP / SYS* congruence checks
* Metadata catalog reports
* Proof that reflected commands, generated HELP, and SYS* tables agree

Secondary active areas:

* CDX / LMDB lifecycle cleanup
* SMARTLIST improvement
* Memo payload/backend proof
* DDL seeding and schema workflow expansion
* Metadata-generated DrawIO diagrams
* Continued TUI cleanup and command-discovery reinforcement
* Browser polish without breaking command semantics

---

## Architecture Overview

```text
xbase/          <- core table engine
xindex/         <- indexing systems
memo/           <- memo subsystem
xexpr/          <- expression engine
cli/            <- command interface, workspace commands, browsers, HELP, DDL, DrawIO helpers
help/           <- reflection and HELP model
tuple/          <- tuple / row / cell / relation-aware adapters
pydottalk/      <- Python bindings
tv/             <- simple TUI components
dottalkpp/      <- runtime data, scripts, workspaces, tests, help
```

---

## Design Rules

* DbArea is the runtime truth for records, cursor, mutation, and table flavor behavior
* Memo payload is external to table engine
* CDX is the logical multi-tag index abstraction
* LMDB is the physical backend, hidden behind normal command-surface wording
* HELP should increasingly be generated or validated from runtime truth
* DotScript is canonical for automation
* Python is a future integration surface
* Tuple infrastructure is relation-aware and orthogonal to raw table storage
* Browsers are first-class inspection surfaces, not just formatted LIST output
* The TUI is a convenience and discovery layer; the command language remains canonical
* Student learning matters: visible layers are a feature, not a flaw

---

## Example Sessions

### x32 MCC relation smoke

```text
do x32
ersatz mcc
ersatz
```

Expected behavior:

```text
WORKSPACE LOAD: restored 12 area(s) and 15 relation(s).
ROWS SHOWN: ... | STATUS: OK
```

### Browser smoke

```text
do x32
ersatz load mcc
ersatz
select students
smartbrowse
simplebrowse
```

Expected behavior:

```text
ERSATZ Relational Browser opens on STUDENTS.
SMARTBROWSE / ARTBROWSE shows interactive record browsing state.
SIMPLEBROWSE emits tuple-style rows from the selected area.
```

### x64 metadata relation smoke

```text
do metadata
workspace open dbf cdx
rel add syscmd syssubcmd on can_name to parent
rel add syssubcmd sysentvar on qual_name to help_ownr
select 1
rel list all
```

Expected relation shape:

```text
SYSCMD
  -> SYSSUBCMD ON can_name TO parent
    -> SYSENTVAR ON qual_name TO help_ownr
```

### x64 metadata relation persistence

```text
workspace save metadata_rel
workspace close
do metadata
workspace load metadata_rel
select 1
rel list all
select 7
rel list all
```

Expected behavior:

```text
WORKSPACE LOAD: restored 8 area(s) and 2 relation(s).
```

### HELP / reflection smoke

```text
help
help functions
help function soundex
cmdhelpchk
cmdhelpchk ref
```

Expected behavior:

```text
HELP displays mixed-source command/function help.
CMDHELPCHK reflection mode reports command, subcommand, and function checks.
```

---

## Roadmap

### Short Term

* CMDHELPCHK / SYS* congruence validation
* HELP metadata alignment
* Preserve asymmetric relation behavior while building reports on top of it
* Continue CDX / LMDB lifecycle cleanup
* Keep x32 MCC regression smoke passing
* Keep browser smoke paths passing
* Keep the simple TUI aligned with real command names

### Mid Term

* Stronger metadata reports
* Generated HELP validation
* SMARTLIST improvements
* Tuple engine stabilization
* Memo backend proof
* DDL seeding improvements
* Browser polish
* Metadata-aware TUI help and command discovery

### Long Term

* Metadata-generated diagrams
* Stronger Python integration
* Service layer experiments
* UI expansion
* Migration and teaching tools
* Better educational labs around tables, indexes, relations, metadata, and HELP validation
* Finished educational tools, database utilities, and applications built on the proven runtime

---

## Naming and Identity

DotTalk++ preserves the spirit of FoxPro/xBase engineering without copying legacy branding.

It values:

* Direct command interaction
* Understandable table files
* Fast inspection
* Scriptable workflows
* Relation-aware browsing
* Self-documenting runtime metadata
* Learning through visible system behavior

The project is not trying to pretend the past was perfect. It is trying to recover the parts that were teachable, direct, and powerful.

---

## Why This Exists

DotTalk++ exists to make database systems understandable again.

It is not trying to be a commercial database product. It is a working educational and research system built around ideas that are still worth teaching:

* records and fields
* table files
* indexes and access paths
* work areas and runtime state
* relations and graph traversal
* commands and scripts
* HELP as part of the system
* metadata as self-description
* HELP and validation as proof

The project draws from xBase, dBase, Clipper, FoxPro, DOS-era command systems, and early personal-computer software because those systems made many of the layers visible.

Modern software often hides those layers.

DotTalk++ tries to expose them again, but with cleaner modern architecture underneath.

Some areas are still beta because they are being proven layer by layer. The goal is to finish useful educational tools, database utilities, and applications from the pieces that prove themselves.

---

## Author

Derald Grimwood  
B.S. Management Information Systems  
xBase / SAP / ERP background

---

## License

(To be defined)

---

## Final Notes

> User interfaces change, languages change, but the underlying database principles remain constant.
>
> — Derald Grimwood

> Preserve the past. Teach the layers. Fix the architecture. Move forward.
````
