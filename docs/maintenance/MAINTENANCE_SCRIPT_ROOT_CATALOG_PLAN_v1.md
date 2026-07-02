# Maintenance Script Root Catalog Plan v1

Status: planning / report-only

## Purpose

DotTalk++ now has multiple SelfDoc and mutable-document maintenance lanes: comments, HELP/CMDHELP/DOTREF, CMDHELPCHK, manualgen, Data Dictionary, messaging, Blackbox education, and future native maintenance surfaces.

This plan defines where maintenance scripts and cookbooks should live before more execution packages are added.

## Root decision

Recommended external maintenance script root:

```text
dottalkpp\scripts\maintenance
```

Reserved native C++ maintenance source root:

```text
src\maintenance
```

Runtime DotScript root, kept separate:

```text
dottalkpp\data\scripts
```

## Doctrine

Scripts maintain. Data records. Source implements. Docs explain. Runtime inspects.

The maintenance root is not a dumping ground. Every script should belong to a lane, have a catalog row, and declare whether it is report-only or mutating.

## Blackbox framing

Each lane is documented as:

```text
DATA IN -> BLACKBOX PROCESS -> INFORMATION OUT
```

with controls for backup, rollback, boundary ledger, smoke proof, and next gate.
