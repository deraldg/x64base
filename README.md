Here is a **production-grade README** tailored to what you’ve actually built—not a generic one. This reflects your architecture, your philosophy (FoxPro lineage without imitation), and the current state of DotTalk++.

You can paste this directly into your GitHub README.md.

---

# DotTalk++ / x64base

**A modern xBase / FoxPro-inspired data engine with a clean architecture, CDX-compatible indexing, and an LMDB-backed storage layer.**

---

## Overview

DotTalk++ is a ground-up reimplementation of the xBase/FoxPro data model with a modern C++20 architecture.

It preserves the **behavioral contract** of classic DBF systems while introducing:

* A structured engine core (`xbase`)
* A clean CLI and scripting layer (DotScript)
* A multi-index architecture (INX / CNX / CDX)
* A scalable backend using **LMDB**
* A forward-compatible memo system
* A path toward relational and tuple-based navigation

This is not an emulator.
It is a **continuation of the lineage**.

---

## Design Philosophy

* Preserve the **engineering behavior** of FoxPro/xBase
* Avoid copying branding or legacy constraints
* Separate **engine, interface, and storage concerns**
* Build a system that can scale from:

  * CLI experimentation
  * → scripting
  * → embedded use
  * → service integration

---

## Current Status

**Engine:** Beta
**Indexing (CDX/LMDB):** Alpha → approaching Beta
**Memo System (x64):** Operational (OO-based)
**CLI / DotScript:** Stable
**Tuple / Relations:** In progress

---

## Key Features

### Core Engine (xbase)

* DBF-compatible table handling
* Multiple table flavors (v32, v64, extensible x64)
* Field-level validation and type support (C, N, F, D, L, M, I, B, Y)
* Cursor-based navigation model

---

### Indexing System

DotTalk++ supports **three parallel indexing models**:

| Type | Purpose                    | Status             |
| ---- | -------------------------- | ------------------ |
| INX  | Legacy/simple index        | Stable             |
| CNX  | Transitional multi-tag     | Stable             |
| CDX  | Modern multi-tag container | Active development |

#### CDX + LMDB Architecture

```
INDEXES/
  students.cdx        ← container (logical)

LMDB/
  students.cdx.d/     ← physical backend
```

* CDX acts as the **user-facing container**
* LMDB provides the **physical storage engine**
* `BUILDLMDB` materializes index data from CDX metadata

---

### Navigation Model

* `SET ORDER TO TAG <name>`
* `TOP`, `BOTTOM`, `SKIP`
* Logical vs physical row tracking
* Ordered traversal via shared iterator layer

SMARTLIST is the canonical display tool.

---

### CLI and DotScript

Interactive shell:

```
DotTalk++ type HELP. USE, SELECT <n>, AREA, COLOR, ABOUT, QUIT
```

DotScript supports:

* Structured programming constructs
* Batch execution
* Educational step-through workflows

---

### Memo System (x64)

Object-oriented design:

```
DbArea → MemoRef → MemoManager → MemoObject → MemoStore
```

Capabilities:

* Multi-record memo isolation
* Persistence across sessions
* Safe PACK behavior with repair handling
* Future-ready for large object storage

---

### Expression Engine (xexpr)

Supports:

* Numeric, string, and date functions
* FoxPro-style expressions
* Runtime evaluation

Example:

```
CALC SOUNDEX("WHITE")
→ W300
```

---

## Command Highlights

### Table Operations

```
USE <table>
SELECT <n>
AREA
STRUCT
```

### Indexing

```
SET INDEX TO students.cdx
SET ORDER TO TAG lname
BUILDLMDB
REINDEX
```

### Navigation

```
TOP
BOTTOM
SKIP
SEEK <value>
```

### Query / Display

```
SMARTLIST
LIST (developer tool)
COUNT FOR <expr>
SCAN / ENDSCAN
LOCATE FOR <expr>
```

---

## SMARTLIST vs LIST

* **SMARTLIST**

  * Table-aware
  * Order-aware
  * Expression-driven
  * Future primary interface

* **LIST**

  * Developer tool
  * Cursor-driven
  * Will be reduced to a simple table printer post Beta-1

---

## Index Lifecycle

```
CDX CREATE
SET INDEX
SET ORDER
BUILDLMDB
→ LMDB backend ready
```

Mutation model (in progress):

* Append / Replace → index update
* Delete / Recall → pending integration
* Buffered vs direct write modes planned

---

## Current Work Focus

* Stabilizing CDX ↔ LMDB lifecycle
* Fixing COMMIT / rebuild locking behavior
* Completing index mutation handling (DELETE/RECALL)
* Making SMARTLIST the primary listing engine
* Improving predicate handling in LOCATE (range conditions)

---

## Architecture Overview

```
xbase/          ← core engine
xindex/         ← indexing systems
memo/           ← memo subsystem
xexpr/          ← expression engine
cli/            ← command interface
pydottalk/      ← Python bindings (optional)
tvision/        ← visual helper shell (optional)
```

---

## Design Rules

* DbArea is the **runtime truth**
* Memo payload is **external to table engine**
* Index containers are **abstracted from backend**
* CLI is canonical for execution
* DotScript is canonical for automation
* Python is canonical for integration

---

## Example Session

```
DO SANDBOX
USE students
SET INDEX TO students.cdx
SET ORDER TO TAG lname

SMARTLIST
```

---

## Roadmap

### Short Term

* Complete index mutation cycle
* Fix LMDB lifecycle (COMMIT / rebuild)
* Normalize predicate behavior

### Mid Term

* Tuple engine stabilization
* Relation-aware browsing
* SMARTLIST enhancements

### Long Term

* Service layer (REST / gRPC)
* Full Python integration
* Enterprise data migration tooling

---

## Naming and Identity

DotTalk++ preserves the **spirit of FoxPro/xBase engineering**
without copying legacy branding.

* Modern typeface: Rajdhani
* Terminology aligned with classic systems
* Architecture designed for forward evolution

---

## Why This Exists

Most modern systems abandoned the simplicity and power of xBase.

DotTalk++ is an attempt to:

* Recover that model
* Cleanly separate concerns
* Make it extensible again
* And prove it still works—at scale

---

## Author

Derald Grimwood
B.S. Management Information Systems
xBase / SAP / ERP background

---

## License

(To be defined)

---

## Final Note

> Preserve the past. Fix the architecture. Move forward.


