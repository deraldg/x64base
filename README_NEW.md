# DotTalk++ / x64base

**A working xBase / FoxPro-inspired database runtime, command shell, and architecture system built in modern C++.**

---

## Overview

DotTalk++ is a C++ database runtime and command system derived from the xBase lineage.

It combines:

- a DBF-compatible data engine
- a command-driven execution environment
- a scripting system (DotScript)
- a relational exploration model
- a metadata and HELP framework

DotTalk++ is a reimplementation of xBase concepts using a modern, layered architecture.

---

## What This Is

DotTalk++ provides a visible, interactive database system where internal behavior is not hidden.

It exposes:

```text
records
fields
indexes
relations
metadata
runtime state
```

The system operates as:

- a working database runtime
- an inspection and teaching environment
- an architecture testbed

---

## Quick Start

```text
DO SANDBOX
USE students
SET INDEX TO students.cdx
SET ORDER TO TAG lname

SMARTLIST
```

---

## Current Status

| Component | Status |
| --- | --- |
| Engine | Stable |
| Indexing (INX/CNX/CDX) | Active |
| LMDB backend | Active |
| Relations | Working |
| Metadata / HELP | Active |
| Browsers | Active (beta) |
| TUI | Experimental |

---

## Core Model

DotTalk++ operates as four layers:

```text
Command Layer      CLI and DotScript
Data Layer         tables, records, indexes
Logic Layer        expressions and validation
Projection Layer   listing, browsing, tuples
```

Each layer has a distinct responsibility.

---

## Architecture Summary

```text
CLI
-> parser
-> command handler
-> DbArea
-> xindex / memo / tuple services
-> output
```

---

## Index Architecture

```text
CDX container = logical index abstraction
LMDB backend  = physical storage implementation
```

Commands operate on CDX. LMDB is internal.

Example:

```text
SET INDEX TO students.cdx
SET ORDER TO TAG lname
BUILDLMDB
```

---

## Navigation

```text
SET ORDER TO TAG <name>
TOP
BOTTOM
SKIP
SEEK <value>
GOTO <n>
```

Logical order is defined by the active order. Physical record order remains unchanged.

---

## Listing and Browsing

| Tool | Purpose |
| --- | --- |
| SMARTLIST | Primary order-aware listing |
| LIST | Developer sequential listing |
| SIMPLEBROWSE | Tuple-style view |
| SMARTBROWSE / ARTBROWSE | Interactive browsing |
| ERSATZ | Relation-aware browser |

---

## Relations

DotTalk++ supports relation graphs between tables.

Same-field relation:

```text
REL ADD students enroll ON SID
```

Asymmetric relation:

```text
REL ADD syscmd syssubcmd ON CAN_NAME TO PARENT
```

Relations persist in workspaces.

---

## Workspace

```text
WORKSPACE SAVE <name>
WORKSPACE LOAD <name>
WORKSPACE CLOSE
```

Workspaces store:

- open tables
- work areas
- relations
- active orders

---

## DotScript

DotScript provides:

- batch execution
- repeatable workflows
- smoke tests
- teaching scripts

Example:

```text
SET ECHO OFF
SET PAGING OFF

DO SANDBOX
USE students
SMARTLIST
```

---

## Metadata and HELP

DotTalk++ implements a reflection-driven system:

```text
runtime -> reflection -> metadata -> HELP -> validation
```

Commands:

```text
HELP
HELP FUNCTION <name>
CMDHELPCHK
CMDHELPCHK REF
```

---

## Command Behavior Specification

### General Rules

Commands operate on the current work area.

Runtime state includes:

- current work area
- cursor position
- active order
- active filter
- relation graph

Commands must not silently modify unrelated state.

---

### SEEK

```text
SEEK <value> [IN <field>]
```

Requires an active table and an active order.

Result:

```text
Found at <recno>
Not found
```

SEEK is a cursor-moving command. If successful, it positions the current record pointer.

---

### SMARTLIST

```text
SMARTLIST [FOR <expr>]
```

SMARTLIST iterates records in logical order.

It respects:

- active order
- active filter
- optional predicate

SMARTLIST restores the cursor after execution.

---

### LIST

```text
LIST [FOR <expr>]
```

LIST is a developer inspection command.

It performs sequential record output and restores the cursor after execution.

---

### REL ADD

```text
REL ADD <parent> <child> ON <field> [TO <target>]
```

REL ADD creates a directed relation edge.

Supported forms:

- same-field relation
- asymmetric parent-field to child-field relation

---

### WORKSPACE

```text
WORKSPACE SAVE <name>
WORKSPACE LOAD <name>
WORKSPACE CLOSE
```

Workspace commands persist and restore runtime state.

---

## Execution Model

All commands follow this execution pipeline:

```text
parse -> validate -> bind -> execute -> resolve -> output -> restore
```

### Stage Responsibilities

| Stage | Responsibility |
| --- | --- |
| Parse | Tokenize input and identify command intent |
| Validate | Check command, argument count, and argument type |
| Bind | Resolve current area, table, fields, order, and services |
| Execute | Perform the core command operation |
| Resolve | Convert internal result to display-ready form |
| Output | Emit deterministic user-facing output |
| Restore | Restore transient state when required |

---

### SEEK Execution

```text
Parse     -> extract value and optional field
Validate  -> ensure table and active order
Bind      -> resolve tag and backend
Execute   -> index seek or fallback scan
Resolve   -> match, near match, or no match
Output    -> result message
Restore   -> none; cursor intentionally moves
```

---

### SMARTLIST Execution

```text
Parse     -> optional predicate
Validate  -> ensure table open
Bind      -> resolve order, fields, and predicate
Execute   -> iterate records
Resolve   -> format rows
Output    -> display rows and count summary
Restore   -> restore original cursor
```

---

### BUILDLMDB Execution

```text
Validate  -> ensure CDX container exists
Bind      -> resolve LMDB backend path
Execute   -> close active LMDB handles and rebuild backend
Resolve   -> verify rebuild result
Output    -> success or failure message
Restore   -> reopen active order if required
```

---

## Cursor Rules

Cursor-moving commands:

```text
SEEK
TOP
BOTTOM
SKIP
GOTO
```

Non-destructive inspection commands:

```text
LIST
SMARTLIST
SCAN
```

Inspection commands must restore cursor position unless documented otherwise.

---

## Engine Binding Specification

The engine binding chain is:

```text
CLI command
-> command parser
-> command handler
-> DbArea
-> xindex / memo / tuple services
-> formatted output
```

---

### DbArea Contract

DbArea owns:

```text
tables
records
cursor
fields
mutation
```

DbArea does not own:

```text
indexes
memo payloads
HELP rendering
browser presentation
output formatting
```

---

### Index Binding

```text
SET INDEX -> CDX container
SET ORDER -> tag activation
         -> LMDB backend bound internally
```

Rules:

- Commands refer to CDX containers and tags.
- LMDB remains a backend implementation detail.
- Ordered traversal uses shared iterator services.
- Commands must not independently parse LMDB files.
- CDX/LMDB attachment and detachment must be centralized.

---

### Memo Binding

```text
Record field -> MemoRef -> MemoManager -> payload
```

Rules:

- DbArea stores memo references only.
- MemoManager resolves content.
- Commands display memo content through memo services.

---

### Tuple Binding

```text
Tuple = projected rows across relations
```

Rules:

- Tuple traversal is relation-aware.
- Tuple output does not mutate source tables.
- Tuple logic remains independent of raw table storage.

---

## Mutation Model

```text
Command
-> DbArea mutation
-> index update
-> memo update
-> output
```

Mutation commands include:

```text
APPEND
REPLACE
MULTIREP
DELETE
RECALL
PACK
ZAP
```

Mutations must pass through DbArea. Index updates must pass through the index subsystem. Memo payload changes must pass through MemoManager.

---

## Commit / Rollback

```text
COMMIT
  apply staged changes
  update indexes
  update memo state
  flush storage

ROLLBACK
  discard staged changes
  restore prior runtime view
```

COMMIT must not rebuild CDX/LMDB as a substitute for normal index updates unless explicitly requested.

---

## Output Rules

Output must be:

- deterministic
- consistent across commands
- independent of execution path

Engine code returns state. CLI code formats output.

---

## Error Rules

Errors must:

- be explicit
- avoid silent failure
- avoid partial state changes
- preserve runtime consistency

Low-level errors flow upward through structured service results and are translated into command output at the CLI layer.

---

## Canonical Ownership

```text
CLI          execution
DotScript    automation
DbArea       table state
xindex       indexing
MemoManager  memo data
Tuple        projections
HELP         documentation
CMDHELPCHK   validation
```

---

## Project Direction

Near-term focus:

- HELP / metadata congruence
- CDX/LMDB lifecycle cleanup
- SMARTLIST improvement
- memo validation
- metadata reports

Longer-term focus:

- stronger metadata reports
- generated HELP validation
- tuple engine stabilization
- DDL seeding improvements
- metadata-generated diagrams
- stronger Python integration
- educational database utilities

---

## Why This Exists

DotTalk++ exposes database systems as working structures.

It makes visible:

```text
records
fields
indexes
relations
metadata
runtime state
```

The system demonstrates how database behavior is constructed rather than hidden.

---

## Author

Derald Grimwood  
B.S. Management Information Systems

---

## Final Note

> Preserve the past.  
> Expose the layers.  
> Fix the architecture.  
> Move forward.
