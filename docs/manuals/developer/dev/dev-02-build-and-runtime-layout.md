# DEV-02 Build and Runtime Layout

```yaml
page_id: DEV-02
title: Build and Runtime Layout
status: DRAFT
last_verified: 2026-05-24
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
