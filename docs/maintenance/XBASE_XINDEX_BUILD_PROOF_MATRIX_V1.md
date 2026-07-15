# xbase / xindex Build Proof Matrix v1

Status: **active; NONE and LEGACY proven, LMDB backend and composition proven**  
Date: 2026-07-14  
Owner: DotTalk++ SDLC build and database proof lanes
Decision authority: `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`

## Current answer

The engine now has three explicit, mechanically different index profiles:

| `DOTTALK_INDEX_MODE` | Build graph | Runtime proof |
| --- | --- | --- |
| `NONE` | `xbase`, `memo`, `xexpr`; no xindex target or library | CLI physical `USE`; Python DBF read/CRUD; `SEEK` absent |
| `LEGACY` | xbase plus xindex without `lmdb_backend.cpp` | CNX attach/order/SEEK returns Anderson; LMDB commands absent |
| `LMDB` | xbase plus complete xindex | full DEVELOPMENT build; CNX navigation; native LMDB persistence smoke |

`xbase.lib` no longer links to or owns xindex. It exposes neutral opaque
mutation hooks. `xindex.lib` depends on xbase, installs those hooks when an
index manager is attached, and owns manager lifetime outside `DbArea`.

One qualification matters: `dottalkpp.exe` still links LMDB independently for
the runtime message catalog. `DOTTALK_INDEX_MODE=NONE` therefore means **no
xindex engine**, not yet **no LMDB runtime dependency anywhere**. The Python
module and xbase library do not need xindex in NONE.

## Current dependency direction

```text
xbase.lib  (physical DBF/record engine; neutral optional hooks)
    ^
    |
xindex.lib (LEGACY or LMDB provider; absent in NONE)
    ^
    |
dottalkpp / pydottalk (composition roots)
```

The old duplicate `src/cli/record_view.cpp` implementation is excluded;
`src/xbase/record_view.cpp` is the single physical implementation.

`USE` does not collapse this boundary. It is a composition-root command whose
index discovery/attachment branches are guarded by `DOTTALK_HAS_XINDEX`. A
NONE build compiles its physical path and omits those branches, the index
commands, the xindex target, and `xindex.lib`. The maintained rationale and
non-claims are recorded in
`docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`.

## Runtime/build evidence

| Capability | State | Evidence |
| --- | --- | --- |
| Clean pydottalk build without xindex | **proven** | `build-proof-table-only`; no xindex target or `xindex.lib` |
| Clean dottalkpp build without xindex | **proven** | `build-proof-table-only/src/Release/dottalkpp.exe` |
| Physical DBF open/read | **proven** | `pydottalk_dbf_readonly_smoke` |
| Physical update/append/delete/reopen | **proven** | disposable-copy `pydottalk_xbase_physical_crud_smoke` |
| NONE command boundary | **proven** | registered profile smoke: table opens; SEEK and BIBLETALK are unknown |
| LEGACY clean build | **proven** | `build-proof-legacy`; xbase and xindex link without LMDB index backend |
| CNX attach/order/SEEK | **proven read-only** | LNAME order, `SEEK ANDERSON`, record 21 returned; fixture hashes unchanged |
| LEGACY command boundary | **proven** | LMDB and BIBLETALK are unknown |
| Full DEVELOPMENT + LMDB composition | **proven** | `build-labtalk` builds xbase, xindex, CLI, TUI, and pydottalk |
| Native LMDB backend | **proven** | open/upsert/duplicates/seek/scan/erase/close/reopen persistence test |
| Product package manifests | **proven** | four validators pass; fresh LEAN install contains ten reviewed files before first launch |
| Installed LEAN runtime | **proven** | app-local `sqlite3.dll` and `lmdb.dll`; SQLite 3.50.4 detected; exit 0; no files created on an idle launch |
| Attached-index mutation synchronization | **not yet isolated** | replace hooks compile; focused append/delete/recall/pack index tests remain |
| CDX metadata-to-LMDB CLI workflow | **not yet isolated** | native backend is proven; full public command workflow needs a fixture test |
| Stale/collation mismatch rejection | **not yet isolated** | contracts exist; focused runtime test remains |

## Registered proof

| CTest | Boundary |
| --- | --- |
| `dottalkpp_profile_smoke` | profile-aware, read-only DBF/CNX hashes; checks NONE/LEGACY/LMDB and lean command leaks |
| `pydottalk_dbf_readonly_smoke` | authoritative DBF fixture read-only |
| `pydottalk_xbase_physical_crud_smoke` | temporary DBF-only copy; no sidecars |
| `dottalkpp_lmdb_backend_smoke` | build/test-local scratch LMDB environment, removed on pass |
| `package_manifest_{lean,professional,educational,development}` | tracked source-input allow-lists and forbidden-path gate |

## Canonical Windows profiles

```powershell
cmake --preset windows-lean-table
cmake --build --preset windows-lean-table --target dottalkpp pydottalk
ctest --preset windows-lean-table

cmake --preset windows-lean-lmdb
cmake --build --preset windows-lean-lmdb --target dottalkpp
ctest --preset windows-lean-lmdb

cmake --preset windows-educational-lmdb
cmake --preset windows-development-lmdb
```

The older `DOTTALK_WITH_INDEX` boolean is now compatibility state:

- `ON` maps to `LMDB`;
- `OFF`, when no explicit new mode is supplied, maps to `LEGACY`;
- only explicit `DOTTALK_INDEX_MODE=NONE` removes xindex.

## Next index proof order

1. Add DBF replace/append/delete/recall synchronization tests with an attached
   CNX index.
2. Add a copied-fixture CDX metadata + LMDB public-command test.
3. Add stale-index and collation-mismatch rejection tests.
4. Move the message-catalog LMDB store behind its own selector if a completely
   LMDB-free CLI is wanted.

Project licensing: To be determined.
