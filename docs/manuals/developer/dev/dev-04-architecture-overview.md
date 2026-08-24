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
