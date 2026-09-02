# Guarded HELP Refresh Package v1

Status: PROPOSED / MUTATION_NOT_AUTHORIZED

## Why a current HELP rebuild is proposed

The live HELP family was last written on 2026-07-07. Messaging/help source inputs are currently modified, the post-messaging usage-contract harvest is newer, and the pre-refresh artifact check reports 461 orphan command keys plus nine compact SET canonicalization errors.

## Conditional command order

```text
if reviewed evidence confirms include/dotref.hpp changed since the legacy build:
    CMDHELP BUILD LEGACY
CMDHELP BUILD . D:\code\ccode\src
```

DOTREF is not currently dirty, so the legacy trigger remains `REVIEW_REQUIRED`; file timestamps are not sufficient evidence.

## Required execution controls

- explicit maintainer authorization
- copy every pre-refresh HELP file named by the protected manifest into a dated backup directory
- hash-verify the backup
- resolve the conditional legacy-build trigger
- run approved build commands only
- capture post-build file and row-count deltas
- rerun CMDHELPCHK reflection, artifacts, and legacy checks

No HELP, DBF, DBT, index, LMDB, source, COMMENTS, manual, or publication file was changed while preparing this package.
