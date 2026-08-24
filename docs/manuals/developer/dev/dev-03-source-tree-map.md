# DEV-03 Source Tree Map

```yaml
page_id: DEV-03
title: Source Tree Map
status: DRAFT_PATCHED
last_verified: 2026-05-24
```

## Key correction

Source is a verification and provenance sidecar. It is not the primary manual-generation source now that HELP/META/CMDHELPCHK mined evidence exists.

## Source estate boundary

```text
D:\code\ccode\src
D:\code\ccode\include
D:\code\ccode\bindings
```

Runtime/data/script estate:

```text
D:\code\ccode\dottalkpp
```

## Major source lanes

| Lane | Primary area | Manual role |
|---|---|---|
| CLI | `src/cli` | command handlers, dispatch, DotScript, HELP bridge |
| HELP / SelfDoc | `src/help`, HELP bridge code | source miner, HELP DATA, validators |
| xBase / DbArea | `src/xbase`, `include/xbase.hpp` | table engine |
| Indexing | `src/xindex`, `src/cnx`, `src/cdx` | orders, tags, CNX/CDX/LMDB |
| Memo | `src/memo` | MemoManager lifecycle |
| Expression | `src/xexpr`, `src/cli/expr` | xexpr and function bridge |
| Relations / tuple | workspace/relation/tuple CLI files | workspace, relations, tuple traversal |
| Browser/TUI | `src/browser`, `src/tv` | projection and UI |
| Bindings | `src/bindings` | optional external integration |
| Common | `src/common` | path state and shared helpers |

## Core rule

Source verifies ownership, handlers, build gates, provenance, and implementation boundaries. HELP and META provide mined evidence. CMDHELPCHK validates reflection. Runtime proof proves behavior. The manuals assemble the result.
