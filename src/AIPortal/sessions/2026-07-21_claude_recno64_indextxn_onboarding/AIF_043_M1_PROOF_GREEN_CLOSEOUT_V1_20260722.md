# AIF-043 M1 — In-Memory Indexed Tables — PROOF GREEN CLOSEOUT

**Status:** ✅ PROVEN GREEN 2026-07-22. **Author:** Claude (steward). **Lane:** AIF-043
(In-Memory Tables & Indexing). **Maintainer-gated:** edits applied to dev working tree;
commit/promote is Derald's call. **Companions:** `VFS_INMEMORY_MILESTONE_PLAN_V1` (plan),
`PROJECT_LANE_IN_MEMORY_TABLES_V1` (charter), `M1_ASSEMBLY_IN_MEMORY_TABLES_V1` (io() seam).

## What was proven

`dottalkpp\data\scripts\mem_proof.dts` runs clean and self-asserts:

- `DO mem` mounts the in-process RAM VFS and points the DBF / INDEXES / LMDB path slots under
  the relocatable `Slot::RAM` root (`data\ram`).
- `CREATE X64 MEMT (ID N(6), LNAME C(20))` builds the table **in RAM** (`is_virtual=1`), and
  USE reopens it **from RAM** — `VDISK STATUS` shows `memt.dbf` as a RAM file, 249 bytes.
- `CDX CREATE` / `CDX ADDTAG LNAME` / `REINDEX CDX` build a **native CDX-V64 (RUN8, uint64
  recno) index in RAM** — `REINDEX: note: native CDX-V64 rebuilt in RAM …` — no LMDB, no env.
- `SET ORDER TAG LNAME` attaches the RAM native CDX; ordered traversal `TOP / SKIP / BOTTOM`
  reads back in index order: **ADAMS, MILLER, ZEBRA** → `MEM_T1/T2/T3 = .T.`.
- Final `VDISK STATUS`: 2 RAM files (`memt.dbf`, `memt.cdx`), **zero files on disk**.

Everything above the byte seam is unaware it isn't a file: identical fixed-width DBF image
(Option A), identical serializer, identical CDX container format.

## Root cause of the multi-cycle CREATE-into-RAM failure (the real story)

The failure — "file written but could not reopen table: DbArea: file does not exist:
…\ram\MEMT.dbf" — was **not** in the engine. `create_dbf` and `DbArea::open` are both in
`xbase.lib`, share one `ramfs` registry, and were handed the identical path string, yet
disagreed on `is_virtual` (create wrote to disk, open read RAM). That is logically impossible
for one function on one registry — which is exactly what pointed past the source into the build.

**The mechanism:** a stale duplicate `src/core/dbf_create.cpp` (no ramfs branch) defines the
same `create_dbf` symbol as `src/xbase/dbf_create.cpp`. The CLI target globs `src/` recursively
and `src/core` was **not** in `_EXCLUDE_DIRS`, so `core/dbf_create.cpp` compiled into the exe's
own object (`build/src/dottalkpp.dir/…/dbf_create.obj`). At link, **an executable's own object
satisfies a symbol before the linker consults a static library**, so the exe ran core's
disk-only `create_dbf` while `open` (which exists *only* in `src/xbase`) used the ramfs branch.
Create→disk, open→RAM. No clean rebuild could surface it because both copies compiled fine;
the tell was `[CREATE-DBG]` present in `xbase.lib`'s `dbf_create.obj` but **absent from the
linked `.exe`**.

**Diagnostic path that nailed it:** temporary `[CREATE-DBG]` / `[SETORDER-DBG]` `cout` probes +
a `ramfs::debug_roots()` snapshot proved the registry was shared and the path normalized under
the mounted root — forcing the conclusion that the *linked* `create_dbf` was a different object
than the *edited* one. `strings` on obj vs exe confirmed the shadow. All probes since removed.

## Fixes landed (dev working tree)

1. **CLI glob exclusion** — `list(REMOVE_ITEM DOTTALKPP_SOURCES … src/core/dbf_create.cpp)` in
   `src/CMakeLists.txt`, mirroring the existing `record_view.cpp` "dead dup" precedent. This is
   the fix that turned CREATE-into-RAM green.
2. **Dup parked** — `src/core/dbf_create.cpp` → `src/core/dbf_create.cpp.bak` so it can no
   longer be globbed. (`fields_mgr.cpp` left in place.)
3. **Ramfs-aware index gates** — replaced disk-only `fs::exists` with ramfs-aware checks:
   - `src/cli/cmd_cdx.cpp` `file_exists()` (CDX CREATE/INFO/TAGS/ADDTAG/DROPTAG).
   - `src/cli/cmd_setorder.cpp` `container_exists()` for the top-level and CDX/CNX activation
     container checks; and the LMDB-env directory check is **skipped for virtual containers**
     (native CDX-V64 has no LMDB env).
4. **Build hardening** (`src/CMakeLists.txt`):
   - **Duplicate-basename shadow guard** — configure-time `FATAL_ERROR` if any CLI source shares
     a filename with an `xbase`/`xindex`/`xexpr`/`value`/`memo` library-owned source. Would have
     caught this class immediately. Verified it passes on the current tree.
   - **`/INCREMENTAL:NO`** on the `dottalkpp` target so a recompiled object is always
     re-embedded into the exe.

## Files touched

- `include/xbase/ramfs.hpp`, `src/xbase/ramfs.cpp` — (probe `debug_roots()` added then removed;
  net no change beyond V1 core).
- `src/xbase/dbf_create.cpp` — probe added then removed (net: the V3 ramfs branch, unchanged).
- `src/cli/cmd_cdx.cpp` — ramfs-aware `file_exists()`.
- `src/cli/cmd_setorder.cpp` — ramfs-aware `container_exists()` + virtual-CDX env-gate skip.
- `src/CMakeLists.txt` — `src/core/dbf_create.cpp` exclusion, shadow guard, `/INCREMENTAL:NO`.
- `src/core/dbf_create.cpp` → `.bak` (parked).
- `dottalkpp/data/scripts/mem_proof.dts` — the self-asserting proof (already present).

## Residual / follow-ups

- **Commit/promote** — maintainer-gated; not done here.
- **Ticket B** (`TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1`) — Option B typed-tuple store, deferred
  to the optimization phase.
- **Optional** `[vdisk]` `.ini` parser for the LMDB-in-RAM symlink add-on — still open, optional.
- Consider auditing whether other `src/core/*` files (e.g. `fields_mgr.cpp`) are live or stale
  duplicates now that the shadow guard exists to flag basename collisions.
