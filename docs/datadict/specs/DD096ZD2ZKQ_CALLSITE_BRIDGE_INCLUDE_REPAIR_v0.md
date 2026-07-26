# DD096Z-D2ZKQ Call-Site Bridge Include Repair v0

Created UTC: `2026-05-29T23:49:22+00:00`

## Purpose

D2ZKQ repairs the D2ZK/D2ZN include mismatch.

D2ZK added bridge helper files and resolver include scaffolding. D2ZN expected `ddict_callsite_bridge.hpp` to be included in `cmd_ddict.cpp`, and correctly refused the safe marker when it was missing.

D2ZKQ inserts only the bridge include when explicitly applied.

## Boundary

No FIELDS/TAGS logic rewrite, no build edits, no active catalog replacement, no active DBF/CDX/LMDB mutation, no HELP/CMDHELPCHK mutation, and no manual mutation.
