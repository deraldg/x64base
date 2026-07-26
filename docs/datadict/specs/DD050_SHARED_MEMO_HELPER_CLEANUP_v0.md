# DD-050 Shared Memo Helper Cleanup v0

Created UTC: `2026-05-28T01:50:31+00:00`

## Purpose

DD-050 cleans up the tactical DD-048 repair by centralizing x64 memo-field storage helper logic.

DD-048 deliberately proved behavior first by adding local IMPORT-side helper logic. DD-050 moves that toward the intended architecture:

```text
one shared CLI helper
IMPORT uses it
REPLACE uses it
ordinary non-memo field behavior preserved
```

## Boundary

Allowed with explicit `--apply-cleanup`:

```text
create include/cli/memo_field_store.hpp
modify src/cli/cmd_import.cpp
modify src/cli/cmd_replace.cpp if safe anchors are found
```

Not allowed:

```text
build
active catalog mutation
datadict_sandbox mutation
probe catalog mutation
HELP/META/CMDHELPCHK mutation
LMDB build
broad IMPORT/REPLACE refactor
```
