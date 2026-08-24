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
