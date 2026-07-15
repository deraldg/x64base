# xbase Optional-Index Architecture Decision v1

Status: **active and implemented**  
Date: 2026-07-14  
Authority: DotTalk++ SDLC engine/build lane  
Project licensing: To be determined.

## Decision

`xbase` is the physical DBF, record, field, memo, and navigation engine.
Indexing is an optional provider above xbase, not an object owned by xbase.

`USE` is a composition-root command. It may contain conditionally compiled
index discovery and attachment code in an indexed product, but that textual
knowledge does not make xbase depend on xindex. In an explicit
`DOTTALK_INDEX_MODE=NONE` build, the xindex branches are not compiled, index
commands are not registered, no xindex target is created, and no `xindex.lib`
is produced or linked.

This is the answer to the concern that `USE` references every supported index:
the command can coordinate optional providers without placing those providers
inside the table engine. The dependency boundary is enforced by the generated
targets, linked artifacts, registered surface, and runtime tests, not by
requiring one universal `USE` source file to be unaware that indexed products
exist.

## Mechanical boundary

```text
xbase.lib
  physical DBF and record behavior
  neutral no-op-by-default index lifecycle hooks
        ^
        |
xindex.lib
  optional CNX/CDX/order manager
  optional LMDB index backend in LMDB mode
  installs xbase hooks when a manager is attached
        ^
        |
dottalkpp / pydottalk
  composition roots select and attach the configured provider
```

The rules are:

1. Public xbase headers and sources do not own or name
   `xindex::IndexManager`.
2. xbase links physical dependencies only; xindex links to xbase.
3. The default xbase hook table is inert, so table operations work without an
   attached index provider.
4. xindex owns manager creation, attachment, close, and lifetime.
5. `DOTTALK_HAS_XINDEX` guards indexed composition code, including the index
   portions of `USE`.
6. NONE supplies physical-order fallbacks and excludes index-only commands.
7. `pydottalk` consumes the same selected engine assembly; it is not the owner
   or superset from which xbase is extracted.

## Supported profiles

| `DOTTALK_INDEX_MODE` | xbase | xindex | LMDB index backend | `USE` behavior |
| --- | :---: | :---: | :---: | --- |
| `NONE` | yes | absent | absent | physical DBF open; no auto-attach; index commands unknown |
| `LEGACY` | yes | yes | absent | physical open plus CNX/CDX/order attachment where available |
| `LMDB` | yes | yes | yes | physical open plus the complete configured index provider |

`USE ... NOINDEX` remains useful in LEGACY and LMDB builds to force physical
order for one open operation. In NONE, physical order is the only compiled
behavior and the keyword is not needed to make the build table-only.

The old `DOTTALK_WITH_INDEX` option is compatibility state only. ON maps to
LMDB; OFF maps to LEGACY unless `DOTTALK_INDEX_MODE=NONE` is explicitly set.
This avoids silently changing the meaning of an older OFF build.

## Proof recorded on 2026-07-14

| Proof | Result |
| --- | --- |
| LEAN + NONE build | CLI and pydottalk built; no xindex target or `xindex.lib` |
| NONE runtime | physical DBF open/read and disposable-copy CRUD pass; SEEK is unknown |
| LEAN + LEGACY build | xindex built with no `lmdb_backend` object |
| LEGACY runtime | tracked STUDENTS CNX attached; LNAME order; SEEK ANDERSON returned record 21; fixture hashes unchanged |
| DEVELOPMENT + LMDB build | full xbase/xindex/CLI/TUI/pydottalk composition built |
| LMDB runtime | native open/upsert/duplicates/seek/scan/erase/reopen persistence smoke passed |
| Registered test totals | NONE 7/7, LEGACY 5/5, LMDB 8/8 |
| Installed LEAN runtime | ten files before and after launch; SQLite 3.50.4 available; exit 0; no empty `.relations` state created |

The installed executable still uses LMDB independently for its message-catalog
mirror. Therefore NONE means no index engine; it does not yet promise that the
entire CLI process has no LMDB runtime dependency. xbase and table-only
pydottalk do not need xindex.

## Non-claims and remaining proof

This decision proves that separation is mechanically possible and implemented.
It does not claim every index mutation path is finished. The next proof work is:

1. attached-CNX replace/append/delete/recall/pack synchronization;
2. a public-command CDX metadata-to-LMDB workflow;
3. stale-index and collation-mismatch rejection;
4. complete HELP/DDICT/function/script component leak checks;
5. a complete built-artifact SBOM and third-party notice bundle.

These are hardening and release-control gates. They do not restore an xbase to
xindex dependency.

## Implementation and evidence pointers

- `include/xbase/index_hooks.hpp`
- `src/xbase/index_hooks.cpp`
- `include/xindex/attach.hpp`
- `src/xindex/attach.cpp`
- `src/cli/cmd_use.cpp`
- `src/cli/index_summary_none.cpp`
- `src/tests/profile_smoke.py`
- `CMakeLists.txt`
- `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`
- `docs/maintenance/SESSION_CLOSEOUT_X64BASE_ENGINE_EDITION_SEPARATION_IMPLEMENTATION_2026-07-14.md`

Development remains authority. This decision does not authorize editing or
reconstructing original work in disposable staging.
