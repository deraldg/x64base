# DD-048 IMPORT Memo Field Assignment Repair Execution v0

Created UTC: `2026-05-28T01:18:37+00:00`

## Purpose

DD-048 applies the guarded source repair for the DD-046/DD-047 finding:

```text
IMPORT appends rows and loads ordinary fields,
but x64 M-field CSV values are imported as blank.
```

## Patch style

DD-048 v0 is a tactical, narrow `cmd_import.cpp` patch:

```text
adds local x64 memo conversion helper
routes M-field CSV values through MemoStore
preserves ordinary a.set(...) behavior for non-memo fields
does not change cmd_replace.cpp
does not add CMake files
```

A later cleanup may extract the helper into shared CLI code after proof is green.

## Required mutation flag

```text
--apply-source-patch
```

Without this flag, DD-048 emits a candidate patch and diff only.

## Boundary

Allowed when explicitly flagged:

```text
modify src/cli/cmd_import.cpp
create backup/diff/report artifacts
```

Not allowed:

```text
build
active catalog mutation
datadict_sandbox mutation
probe catalog mutation
HELP/META/CMDHELPCHK mutation
CDX creation
LMDB build
broad IMPORT refactor
```
