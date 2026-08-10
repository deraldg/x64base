# In-Memory Indexed Tables — VFS Milestone Plan (V1–V5)

**Status:** APPROVED by Derald 2026-07-21 (report-only session; edits applied to dev working
tree, maintainer-gated for commit/promote). **Author:** Claude (steward). **Lane:** AIF-043
(In-Memory Tables & Indexing). **Companions:** `PROJECT_LANE_IN_MEMORY_TABLES_V1` (charter),
`M1_ASSEMBLY_IN_MEMORY_TABLES_V1` (io() seam), `TICKET_B_...` (deferred typed-store),
`AIF_043_RAM_DBF_POSITIONING_AND_LIMITATIONS_V1` (honest peer-set / non-goals / limits).

> **✅ M1 PROVEN GREEN — 2026-07-22.** `mem_proof.dts` passes clean: an x64 table **and** its
> native CDX-V64 index are built, indexed, and traversed entirely in RAM (`xbase::ramfs`),
> ordered read-back returns `ADAMS/MILLER/ZEBRA` (`MEM_T1/T2/T3 = .T.`), with **zero files on
> disk** and no LMDB. Root cause of the multi-cycle CREATE-into-RAM failure was **not** engine
> code: a stale duplicate `src/core/dbf_create.cpp` was globbed into the CLI exe and its object
> silently won the link over `xbase.lib`'s ramfs-aware `create_dbf` (exe object shadows the
> static-lib member), so CREATE wrote to disk while USE read RAM. Fixed by excluding the dup
> from the CLI glob (mirroring the `record_view.cpp` precedent); the dup is now parked to
> `src/core/dbf_create.cpp.bak`. Four further disk-only gates were made ramfs-aware
> (`cmd_cdx::file_exists`, and `SET ORDER`'s container + LMDB-env checks). Build hardened with a
> configure-time duplicate-basename shadow guard and `/INCREMENTAL:NO`. Full writeup:
> `AIF_043_M1_PROOF_GREEN_CLOSEOUT_V1_20260722`.

## Intent (what we are building and why this shape)

An **in-memory indexed table**: rows *and* their native index both resident in process
memory, activated by a `DO mem` environment flavor, with everything above the byte seam
unaware it isn't a file. Substrate = **Option A** (RAM tables stored as the same fixed-width
DBF rows the engine already uses) over a self-owned **`xbase::ramfs`** virtual filesystem —
no third-party RAM-disk driver, no license exposure. LMDB-in-RAM stays a deferred symlink
add-on (LMDB needs a real mmap); **native CDX is the M1 index path** because it is
`ramfs`-routable.

**Grounding finding (2026-07-21, corroborates Derald):** native indexing is already
*in-memory-first*. `BPlusTreeBackend` (`src/xindex/bptree_backend.cpp`) holds the whole index
as an ordered in-RAM `map_`; `seek`/`scan` run on that map; `saveToFile`/`load` only
serialize/deserialize. So "native CDX in RAM" is **redirect the index-file bytes to `ramfs`
(or skip persistence for ephemeral)** — not a rewrite.

**Transparency invariant (why each drop is safe):** no `ramfs` root is mounted until V5, so
`ramfs::is_virtual()` is always false and every virtual branch is dead code until then. Each
drop is byte-identical to today's engine and builds green independently; V5 is what turns it on.

## Milestones

### V1 — `xbase::ramfs` core — DONE (built + self-tested)
Path-keyed RAM files, a random-access memory `streambuf`, mount/registry API
(`include/xbase/ramfs.hpp`, `src/xbase/ramfs.cpp`). Compiled under MSVC (in `xbase.lib`) and a
sandbox self-test exercised write/seek/offset-read/overwrite/grow/reopen/teardown.

### V2 — Route `DbArea` open + record I/O through `ramfs` — WRITTEN (awaiting build)
Loaders widened `std::fstream&`→`std::istream&` (`xbase_vfp.hpp`, `xbase_64.hpp`);
`readHeader`/`readFields` route via `io()`; `DbArea::open` gained a virtual-path branch
(binds `_ram` to a `ramfs` file); `xbase.hpp` seam swapped the drop-1a `_mem` stringstream for
`std::unique_ptr<std::iostream> _ram`; `close()` releases it. This is the one full-rebuild drop
(edits `xbase.hpp`, included by 317 TUs). Gate: `REGRESSION ALL` + `INDEX_X64/X32` green.

### V3 — Create into RAM + locks — NEXT (small, mechanical)
- `dbf_create.cpp` `write_x64_dbf`: virtual branch opens a `ramfs` stream (`create=true`) and
  feeds `serialize_x64_dbf(std::ostream&)` (already extracted, drop 1b-i); skip
  `create_directories` + memo sidecar (memo out of M1 scope).
- `xbase_locks.cpp`: `RLOCK`/`FLOCK`/`UNLOCK` short-circuit to success when `_in_memory`
  (process-local table; no OS handle). Lock file today is `std::ofstream` (line 132).
- After V3: `CREATE X64` + `USE` + `APPEND`/`REPLACE`/nav work against RAM — a working
  **unindexed** in-memory table. Gate: green + transparent (no root mounted yet).

### V4 — Native index in RAM — THE MILESTONE  (BUILD FOR BIG, fall back for small)

**Principle (Derald 2026-07-21): build for big, fall back for small.** Build the native index
for the **big** case — x64 / uint64 recno — and let the **small** case (x32 / uint32) fall back
through the same path. Do *not* cap M1 at x32/CNX just because CNX is what exists today.

**Scout result.** No backend factory; selection is hard-coded by file extension in
`IndexManager` (`index_manager.cpp:191` `openCdx`→LMDB `CdxBackend`; `:228` `openCnx`→native
`CnxBackend`). Native **CNX (x32/uint32)** is the working native sorted path (`CnxDocument`
holds tags+RUN payloads in memory, `CnxBackend` = multi-tag `ITagBackend` serves from RAM).
Native **CDX (x64/uint64)** is format-present / key-path-absent — the twin of CNX (identical
container but for magic + recno width). CDX's key *storage* is what went to LMDB. Confirmed in
`XIDX_NATIVE_FORMAT_FINDINGS_V1`. The native `cdxfile`/`cnxfile` layer is **one `std::fstream`
handle** (`src/cdx/cdx_file.cpp`, ~15 seek/read/write sites; cnx twin identical).

**Approach — pull in `XIDX-NATIVE-CDX-01` (the native CDX V64 key store):**
1. **Widen the RUN payload `InxPayload` to uint64 recnos** (a V64 run format); uint32 CNX reads
   as the fallback. This is the substantive "build for big" piece (recno width lives here).
2. **`CdxDocument`** = twin of `CnxDocument` (`"CDX1"`, uint64 via InxPayload V64).
3. **Native CDX backend** = twin of `CnxBackend` serving uint64 — multi-tag `ITagBackend`, no
   LMDB. (New class; `CdxBackend` name stays the LMDB one.)
4. **Route the shared `cdxfile`/`cnxfile` `std::fstream` handle through `ramfs`** — the same
   one-handle `io()` seam applied to `DbArea` in V2.
5. **Selection:** a virtual (RAM) table's index → native CDX backend (uint64), not LMDB; x32
   falls back to CNX. Flip V3's create guard (x64 primary, x32 fallback — row storage is
   flavor-agnostic; the x32/VFP writer gets the same `ramfs` branch as x64).
   Gate: create an **x64** RAM table, build a native CDX tag, ordered `TOP/BOTTOM/SKIP` over the
   in-RAM **64-bit** index; x32+CNX proven as the fallback.

**Constraint retired:** no 32-bit recno cap — the native in-RAM index is uint64; x32/CNX is the
narrower fallback, not the ceiling. (Native CNX/CDX container offsets stay uint32 file-local;
only the recno *values* widen.)

**Superseded framings:** the orphaned `BPlusTreeBackend` (single-index, u32-persist) and the
x32-only-CNX plan. `XIDX-NATIVE-CDX-01` is no longer deferred — it *is* V4's core.

**Effort note (honest):** the container twin is nearly free (`cdxfile::` already exists); the
real work is (1) InxPayload uint64 runs and (2) the `CdxDocument` + native-backend twins. This
makes V4 a small sub-lane (V4a InxPayload64 → V4b CdxDocument → V4c native CDX backend → V4d
ramfs routing → V4e selection + V3 guard flip → V4f proof), each build-checkpointed.

### V5 — Activation + proof
- `VDISK MOUNT` command (registered like any command): resolves the current DBF/INDEXES slot
  roots to absolute and calls `ramfs::mount`. `mem.dts` gains that line after its `SET PATH`s;
  `DO x64` / `VDISK UNMOUNT` calls `ramfs::clear` — the ephemeral teardown.
- Proof `.dts` (`REGRESSION MEM_TABLE`, out of default suite): `DO mem` → `CREATE X64` →
  `APPEND` w/ dup → `CDX`/`ADDTAG` → assert ordered nav → assert **no real file on disk** →
  `DO x64` → RAM table gone. Open item: the "no real file" assertion mechanism (reuse an
  existing `FILE()`/`EXISTS` predicate if present, else add a small `VDISK LIST`/`STAT`).
  Gate: `REGRESSION ALL` green + `MEM_TABLE` all `.T.`.

## Risk map (honest)

V3 quick, V5 small plumbing + proof, **V4 is the milestone** (backend-selection decision +
widest routing). Highest-uncertainty item is the V4 backend-selection scout — done before any
V4 edit. Everything stays green drop-by-drop via the transparency invariant.

## Out of scope / deferred
Memo-in-RAM (later milestone), LMDB-in-RAM (optional symlink add-on), Option B typed-store
(optimization-phase ticket), the `bptree` `write_u32` recno truncation (folds to AIF-027).
