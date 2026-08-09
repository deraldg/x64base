# Project Lane Charter — In-Memory Tables & Indexing

**Proposed AIF:** AIF-043 (next-free above the AIF-042 ceiling; maintainer assigns final —
note the earlier tentative 043 earmark for a SET INDEXTXN filing, never entered).
**Structure (AIF-040):** Project ⊃ Lane ⊃ Milestone. **Stage:** proposal / charter (report-only).
**Author:** Claude (steward) · **Authority:** Derald · **Date:** 2026-07-21.
**X-links:** AIF-027 (RECNO64 — prerequisite for large in-memory tables), AIF-023/017 (WAL —
durability path), SET INDEXTXN M1 (in-COMMIT index maintenance — composes directly).

## Vision

Memory-optimized tables where the **rows (typed tuples) and their index both live in RAM**,
with a selectable durability model, served by either the **CDX-over-LMDB** backend or a
**native CDX** B-tree — both RAM-backed. The typed-tuple system remains the schema/typing
carrier; in-memory tables are the same fixed-length record shape, just not file-backed.

## Prior art (this is a mainstream advanced-DB feature)

SQL Server In-Memory OLTP (Hekaton) — memory-optimized tables + RAM hash/range indexes,
lock/latch-free. Oracle Database In-Memory (columnar) + TimesTen (full in-memory RDBMS).
SAP HANA (in-memory columnar). MySQL `MEMORY`/HEAP engine. SQLite `:memory:`. Postgres
`UNLOGGED`/`TEMP`. VoltDB, SingleStore, Aerospike, Redis. The recurring axes: where rows
live, where the index lives, and the durability spectrum (ephemeral → snapshot → WAL).

## Why DotTalk++ is well-positioned

- **Fixed-length record layout** — trivially arena/slab-friendly; no variable-record packing.
- **LMDB is already memory-mapped** — "LMDB in RAM" is mostly a matter of backing the env
  with a RAM filesystem (tmpfs / `/dev/shm`) or `MDB_WRITEMAP|MDB_NOSYNC` — near-zero new
  index code; the composite-key `base‖recno8` + `index_hooks` machinery works unchanged.
- **SET INDEXTXN (M1) composes directly** — incremental in-COMMIT maintenance on a RAM
  index is the natural pairing (no BUILDLMDB, mutate-in-place in memory).
- **WAL already exists** (AIF-017/023) — gives an off-the-shelf durability option.
- **RECNO64 (this session) is a prerequisite** — big in-memory tables blow past 2^31.

## Design surface (options, not decisions — see "Decisions needed")

### A. Row storage
- **A1 — RAM-backed DBF arena (recommended M1):** back the existing DBF fixed-length record
  path with an anonymous/private mmap (or `/dev/shm` file). The DBF read/write/navigation
  code runs unchanged; only the "open" path chooses a RAM buffer instead of a disk file.
  Lowest-risk, reuses the whole stack.
- **A2 — Pure arena adapter:** a `std::vector`/slab of fixed-length records behind a thin
  `DbArea`/DBF-interface shim. Cleaner conceptually, more new surface.

### B. Index backend (both RAM)
- **B1 — CDX-over-LMDB in RAM (recommended M2):** env on tmpfs/`/dev/shm`, or
  `MDB_WRITEMAP|MDB_NOSYNC`, or anon-mmap env. Reuses `CdxBackend` + `index_hooks` +
  (optionally) SET INDEXTXN in-COMMIT maintenance verbatim.
- **B2 — Native CDX B-tree in RAM:** build the B-tree in a memory arena instead of the
  `.cdx` file. More work (native CDX is file-format-oriented); a later milestone.

### C. Durability spectrum (the pivotal choice)
- **C1 — Ephemeral:** table + index vanish on CLOSE/exit. Fastest; temp/scratch/analytics.
- **C2 — Snapshot/checkpoint:** materialize to `.dbf`/`.cdx` on demand or at close;
  reload on open. "Load hot, persist cold."
- **C3 — WAL-backed:** journal mutations (existing WAL) so an in-memory table is
  recoverable/durable while running at RAM speed. Composes with SET INDEXTXN.

### D. Declaration / lifecycle (surface syntax)
Candidates: `CREATE MEMORY <table> (...)`, `USE <table> IN MEMORY`, a `MEMORY` path flavor
(alongside x64/x32/SANDBOX), or a `SET MEMORY ON` session mode. Also: a flavor tag
(`v64-mem`?) so STATUS/ABOUT and the workspace report reflect RAM residency.

## Proposed milestones

- **M1 — Ephemeral in-memory table (rows only).** RAM-backed DBF arena (A1, C1). Proof:
  `CREATE MEMORY`, `APPEND`, `REPLACE`, `LIST`, `TOP/BOTTOM/SKIP/GOTO` — all against RAM,
  ERASE-free, gone on CLOSE. Regression: a self-asserting `.dts` (fixture-free, WAL-style).
- **M2 — RAM index (LMDB).** Attach a CDX-over-LMDB index on a RAM env (B1) to the M1
  table; `SEEK`/ordered nav; compose with `SET INDEXTXN` in-COMMIT maintenance. Proof:
  buffered REPLACE+COMMIT reflected by SEEK with no BUILDLMDB, entirely in RAM.
- **M3 — Durability.** Add C2 (snapshot to `.dbf`/`.cdx`) and/or C3 (WAL-backed recovery).
  Proof: mutate in RAM → snapshot → reopen → state preserved; and/or WAL replay.
- **M4 — Native CDX-in-RAM (optional).** B2 for the native path.
- **M5 — Typed-tuple + relations polish.** Tuple projection, REL ENUM/JOIN over in-memory
  tables; confirm provenance fragments carry RAM-residency cleanly.

## Decisions — RE-FLIPPED & LOCKED 2026-07-21 (maintainer) — IN-PROCESS VFS PRIMARY

The symlink pivot (below) was itself re-decided after weighing the **redistribution licensing**
of Windows RAM-disk drivers. A modern Windows RAM disk is a *signed kernel driver* (the trivial
DOS `RAMDRIVE.SYS`/`VDISK.SYS` concept, made heavy by NT's driver-signing) — so every option
drags a third-party license (ImDisk core = permissive; **ImDisk Toolkit = GPL**; OSFMount =
proprietary). That's an external dependency to vet for every distribution. The concept is
1980s-old and doesn't warrant it.

**Final M1 substrate: the self-owned in-process VFS.** The engine already funnels record I/O
through one seam; for the DBF + native-CDX lane, "RAM disk" is just our own byte buffers in
process memory — **no OS driver, no drive letter, no license to vet.** This is `RAMDRIVE.SYS`
owned by the program instead of the OS. It puts us back in the driver's seat (Derald).

1. **Substrate (M1):** **In-process RAM filesystem** (`xbase::ramfs`) — path-keyed byte files
   served from process memory. DBF + native CDX in RAM with zero third-party dependency;
   portable to a bare Windows box (no RAM disk needed).
2. **LMDB (M2):** LMDB *must* mmap a real OS file, so it can't live in the in-process VFS.
   The **symlink/RAM-disk route is demoted to an optional add-on** *only* for LMDB-in-RAM,
   for users who already have (or want) a RAM disk. Not required for M1; not on the critical
   path. `mem.dts` + `Setup-VDisk.ps1` + `VDISK_RAM_SIZING_AND_ADMIN_CONFIG_V1` are retained
   for that optional path.
3. **Tuple system untouched** (projection layer, confirmed) — unchanged from the pivot.
3a. **Row representation (M1) = Option A — RAM bytes** ✅ (locked 2026-07-21). The in-memory
   table is a contiguous byte buffer byte-identical to a `.dbf`, storing exactly the fixed-width
   rows the tuple system builds — so recno nav, CDX, INDEXTXN, commands, snapshot all run
   unchanged. **Option B** (typed tuple vector *as* the store — native/columnar, à la
   Hekaton/HANA) is **ticketed for the optimization phase**, not rejected — see
   `TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1`. B ships on top of a working A, where its
   no-re-parse / columnar wins pay for the nav+index rebuild it requires (and it touches the
   maintainer-owned tuple core).
4. **Reuse already landed:** `serialize_x64_dbf(std::ostream&)` (drop 1b-i) lets `create_dbf`
   write a table straight into a RAM file; the drop-1a `io()`/`_mem` seam is the record-I/O
   routing point. Both are now *on* M1's critical path (not deferred).
5. **Activation surface:** `DO mem` mounts the virtual roots (via a small `VDISK`/mount hook)
   and points the DBF/INDEXES slots at them; normal `CREATE X64`/`USE` then land in RAM.

### VFS drop plan — APPROVED by Derald 2026-07-21

Full intent + per-drop files/seams/risks recorded in `VFS_INMEMORY_MILESTONE_PLAN_V1`.
Transparency invariant: no `ramfs` root is mounted until V5, so every virtual branch is dead
code until then — each drop builds green independently and is byte-identical to today.

- **V1 — `xbase::ramfs` core** — ✅ **DONE** (built in `xbase.lib` + sandbox self-tested).
- **V2 — DbArea open + record I/O via ramfs** — ✍️ **WRITTEN, awaiting build** (loaders widened
  to `std::istream&`; `open()` virtual branch; `_ram` seam in `xbase.hpp`; the one full rebuild).
- **V3 — create into RAM + locks** — NEXT: `write_x64_dbf` virtual branch feeds
  `serialize_x64_dbf` (1b-i); `RLOCK`/`FLOCK`/`UNLOCK` short-circuit when `_in_memory`.
- **V4 — native index in RAM** — THE MILESTONE. **Grounding finding:** native indexing is
  already in-memory-first — `BPlusTreeBackend` holds the index as an in-RAM `map_`;
  `saveToFile`/`load` are the only file touch. So V4 = (1) select the **native** backend for
  mem tables (not LMDB), (2) route its `saveToFile`/`load` through a `ramfs`-aware open helper.
- **V5 — `DO mem` activation + proof `.dts`:** `VDISK MOUNT` hook + `REGRESSION MEM_TABLE`
  proof (CREATE/APPEND/CDX/ordered-nav in RAM, **zero real files on disk**, gone on unmount).

## Decisions — SUPERSEDED 2026-07-21 — SYMLINK PIVOT (retained for provenance)

The M1 substrate was re-decided after a source-read of the tuple system and a co-planning
exchange. The originally-locked "byte-store abstraction + `CREATE MEMORY` verb" (below) is
**superseded for M1** by a **symlink / RAM-disk environment** approach — chosen for maximum
capability at minimum engine surface ("big haul, little effort"):

1. **Substrate (M1):** **Symlink to a RAM-backed volume**, not an in-process VFS. The
   virtual-disk root is an OS symlink/junction to a RAM filesystem (Linux `/dev/shm` tmpfs;
   Windows a RAM-disk driver, e.g. ImDisk). The engine writes ordinary `.dbf`/`.cdx` files
   into it — **zero new record/create/loader code**. Activated the `DO x64` way: a `mem`
   path-slot flavor (`data/scripts/mem.dts`).
2. **LMDB rides for free.** Because the files are real files on a RAM fs, LMDB (which must
   mmap a real file) is RAM-resident too — so this **collapses M1+M2**: DBF **and** native
   CDX **and** LMDB all in RAM via one env trick. The in-process VFS could not host LMDB.
3. **Tuple system untouched.** Source-read confirmed `DbTupleStream`/`TupleRow` are the
   *projection/nav/filter* layer that reads **from** an area — not a storage substrate. It
   consumes a RAM-resident table exactly as a file table, unchanged. (Near-and-dear: safe.)
4. **In-process VFS = deferred upgrade.** The pure "no files, RAM byte buffers" engine
   feature (portable to a bare Windows box with no RAM disk) remains a valid *later* upgrade;
   the `serialize_x64_dbf(std::ostream&)` split already landed (drop 1b-i) is its foundation.
   Modularity by design: swap the substrate later without touching callers.
5. **RAM-size policy — two layers, admin-configurable** (see
   `VDISK_RAM_SIZING_AND_ADMIN_CONFIG_V1`): a provisioning *recommendation* (auto clamp:
   `clamp(25%·avail, 64 MB, 2 GB)` ∧ ≤ 50%·total) and an engine-side *soft budget* monitor
   (`warn_pct`, `on_full = warn|spill|fail`), both driven by an `[vdisk]` block in `init.ini`.
6. **Extras fall out of the design (Derald):** `on_full = spill` **is** "convert RAM → disk";
   a future `VDISK SNAPSHOT`/persist verb **is** "save the whole show" (copy the RAM root to
   a real dir, or pack as a memo/archive). Logged as M3 hooks, not M1 scope.

### Superseded (original M1 lock, retained for provenance)

1. **Durability (M1):** **C1 ephemeral** ✅ — RAM only, gone on CLOSE; snapshot/WAL layer in M3.
2. **First index backend:** **B1 LMDB-in-RAM** ✅ — reuses CdxBackend + index_hooks +
   SET INDEXTXN verbatim.
3. **Row storage:** ~~**A1 RAM-backed DBF** via a byte-store abstraction over the single
   `std::fstream _fp` seam~~ — superseded by the symlink substrate for M1; kept as the
   deferred in-process-VFS upgrade (decision 4 above).
4. **Declaration surface:** ~~`CREATE MEMORY <table>`~~ → **`DO mem`** path-slot flavor
   (mirrors `DO x64`), consistent with the existing environment idiom. `CREATE MEMORY` no
   longer needed — normal `CREATE X64`/`USE` against the `mem` flavor land in RAM.

**M1 assembly (source-grounded) is in `M1_ASSEMBLY_IN_MEMORY_TABLES_V1_20260721.md`:** the
`DbArea` byte store is one `std::fstream _fp` (xbase.hpp:355) that all record I/O routes
through — so in-memory needs only a `MemByteStore` behind an `IByteStore` seam, no
record/schema/nav changes. Windows note: no `/dev/shm`, so the M2 RAM index uses an LMDB
temp env with `MDB_NOSYNC` (RAM-speed, dropped on close).

## Governance / non-goals

Report-only proposal; the maintainer promotes into the intake queue / `projects.yaml` /
dashboard and assigns the authoritative AIF number. Not started. The tuple-system *core*
(`DbTupleStream`) is treated as maintainer-owned (per the 2026-07-21 note) — M5 touches it
only with explicit direction. RECNO64 tail lanes remain independent.
