# Session Closeout: x64base Engine and Edition Separation Implementation

Date: 2026-07-14  
Status: **core implementation and proof complete; focused hardening backlog recorded**  
Authority worked: `D:\code\ccode` only  
Promotion/staging: not run; `C:\x64base` was not touched

## Resume in one minute

The feared dependency is removed: `USE` no longer makes xbase depend on every
supported index. `xbase.lib` is now the physical DBF/record engine with neutral
optional index hooks. `xindex.lib` attaches above xbase and owns index-manager
lifetime. A NONE build has no xindex target or library; a LEGACY build keeps
CNX/order services without the LMDB index backend; an LMDB build keeps the full
provider.

Product composition is independent of index mode. LEAN retains a small
education-essentials surface and excludes full LabTalk, seasonal, Bible, ERP,
MCC, history, external-tool, maintenance, and development command/source
groups. EDUCATIONAL and DEVELOPMENT restore progressively broader components.

Project licensing: To be determined.

## Authoritative selectors

```text
DOTTALK_INDEX_MODE = NONE | LEGACY | LMDB
DOTTALK_PRODUCT    = LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT
```

Compatibility behavior is deliberate: old `DOTTALK_WITH_INDEX=ON` maps to
LMDB; old OFF maps to LEGACY unless the new selector explicitly says NONE.

## Proven matrix

| Profile | Build/runtime proof | Result |
| --- | --- | --- |
| LEAN + NONE | clean CLI and pydottalk build; no xindex target/library; physical DBF read/CRUD; SEEK and BIBLETALK absent | pass |
| LEAN + LEGACY | xindex without `lmdb_backend.cpp`; tracked STUDENTS CNX attached; LNAME order; SEEK ANDERSON returns record 21; LMDB and BIBLETALK absent | pass |
| DEVELOPMENT + LMDB | xbase, xindex, CLI, Turbo Vision, and pydottalk build; CNX navigation; native LMDB duplicate/seek/scan/erase/reopen smoke | pass |
| Product manifests | LEAN, PROFESSIONAL, EDUCATIONAL, and DEVELOPMENT tracked-input validators | pass |
| Source policy | project status wording and source-policy checks | pass |

The profile smoke hashes the authoritative DBF/CNX fixtures before and after;
the read-only tests leave them unchanged. Physical CRUD and LMDB persistence
tests use disposable build-local copies/scratch and remove them after success.

## Installed LEAN package proof

A fresh `build-proof-table-only\installed-lean-v5` install contains ten files
before first launch:

- `bin/dottalkpp.exe`, `lib/pydottalk.cp313-win_amd64.pyd`;
- `bin/dottalkpp.ini`, `bin/init.ini`, `bin/shutdown.ini`;
- `bin/lmdb.dll`, `bin/sqlite3.dll`;
- `LICENSE`, `product.manifest`, `product-inventory.json`.

The first install attempt exposed Windows error `0xC0000135`: the executable's
runtime DLLs were not all installed. CMake now installs the target runtime DLL
set and the app-local SQLite DLL. The isolated installed executable reports
SQLite available at version 3.50.4 and exits zero.

Two adjacent startup defects were also corrected: lock cleanup now treats a
missing DBF directory as an empty set, and relations autosave does not create
an empty `.relations` file unless a relation file already exists. The final
default launch creates no files: ten before, ten after.

The source-input inventories currently contain:

| Product | Tracked inputs | Bytes |
| --- | ---: | ---: |
| LEAN | 3 | 170 |
| PROFESSIONAL | 3 | 170 |
| EDUCATIONAL | 77 | 42,985,211 |
| DEVELOPMENT | 153 | 43,917,015 |

PROFESSIONAL intentionally remains the same minimal payload as LEAN until its
neutral production data/HELP set is classified; it is a named boundary, not a
finished differentiated offering.

## Main implementation locations

- Engine seam: `include/xbase/index_hooks.hpp`, `src/xbase/index_hooks.cpp`
- Provider attachment: `include/xindex/attach.hpp`, `src/xindex/attach.cpp`
- Build/product selectors: `CMakeLists.txt`, `src/CMakeLists.txt`, `CMakePresets.json`
- NONE fallback: `src/cli/index_summary_none.cpp`
- Profile proof: `src/tests/profile_smoke.py`, `src/tests/CMakeLists.txt`
- Package allow-lists: `config/package/*.manifest`
- Package validator: `tools/packaging/build_product_inventory.py`
- Optional-index decision: `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`
- Current proof matrix: `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`
- Full plan and remaining gates: `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md`

## Remaining hardening, in order

1. Add copied-fixture tests for replace/append/delete/recall/pack while a CNX
   index is attached; prove keys and record order remain synchronized.
2. Add a public-command CDX metadata-to-LMDB test, not only the native backend
   unit smoke.
3. Add stale-index and collation-mismatch rejection tests.
4. Extend component identity and leak checks into HELP, DDICT, function, and
   script catalogs.
5. Generate a complete built-artifact SBOM and exact third-party notice bundle;
   the present JSON inventory covers tracked source inputs only.
6. Move the independent message-catalog LMDB store behind its own selector if
   a completely LMDB-free CLI is required. NONE already means no index engine,
   but the CLI still uses LMDB for that separate store.

## Safe continuation commands

```powershell
cmake --preset windows-lean-table
cmake --build --preset windows-lean-table --target dottalkpp pydottalk
ctest --preset windows-lean-table

cmake --preset windows-lean-lmdb
cmake --build --preset windows-lean-lmdb --target dottalkpp
ctest --preset windows-lean-lmdb
```

Do not rebuild or edit staging as part of the next proof pass. Commit original
work in development first; promotion remains a later reviewed human step.
