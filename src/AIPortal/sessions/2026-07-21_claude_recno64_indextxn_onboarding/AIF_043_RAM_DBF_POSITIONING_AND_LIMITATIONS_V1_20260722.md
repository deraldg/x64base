# AIF-043 — RAM DBF: Honest Positioning, Limitations & Comparisons

**Status:** Evaluation / positioning note (not a spec). **Author:** Claude (steward), reviewed
with Derald. **Lane:** AIF-043 (In-Memory Tables & Indexing). **Companions:**
`VFS_INMEMORY_MILESTONE_PLAN_V1`, `PROJECT_LANE_IN_MEMORY_TABLES_V1`,
`AIF_043_M1_PROOF_GREEN_CLOSEOUT_V1_20260722`, `TICKET_B_TUPLE_NATIVE_INMEMORY_STORE_V1`.

> Purpose: put the scope of the RAM DBF on the record — what it is, what it deliberately is
> **not**, and how it honestly compares to established in-memory / advanced database solutions —
> so future work is measured against the right peer set instead of the wrong one.

## 1. What the RAM DBF actually is

An **in-process RAM filesystem** (`xbase::ramfs`) that stores **byte-identical DBF row images**
(Option A) and builds a **native CDX-V64 B-tree index in RAM** (RUN8, uint64 recno). It is
single-process, single-threaded (M1), ephemeral (dropped on `VDISK UNMOUNT` / session end), and
activated by `DO mem`. Its defining property: it sits **beneath the engine's `io()` byte seam**,
so the entire existing xBase command surface — navigation, SEEK, ordered traversal, REL joins,
aggregates — operates unchanged, unaware it is not a file.

**This is not a new database. It is a transparent RAM substrate for a database engine that
already existed.** That framing determines the correct peer set.

## 2. Peer set (what to compare against) and non-goals

**Correct peers:** SQLite `:memory:`; a tmpfs / RAM-disk holding the engine's own DBF/CDX; the
1980s RAMDRIVE.SYS/VDISK.SYS pattern (self-owned, in-process instead of a kernel driver).

**Wrong peers (explicit non-goals — do not benchmark against these):**
- Distributed / clustered in-memory OLTP: SingleStore (MemSQL), VoltDB, SAP HANA.
- Columnar / vectorized OLAP: DuckDB, ClickHouse, kdb+.
- General multi-user RDBMS: PostgreSQL, SQL Server, Oracle.
- KV / cache stores: Redis, Memcached.

The RAM DBF is **not** trying to win concurrency, durability, SQL optimization, analytical
throughput, or horizontal scale. It targets ephemeral single-process in-memory tables with a
native ordered index, full engine transparency, and zero third-party/licensing exposure.

## 3. Where it genuinely wins

- **Transparency / leverage.** ~250 lines of `ramfs` lit up the complete command surface in
  RAM with no query-layer rewrite. Very high capability-to-code ratio.
- **Format fidelity.** The RAM image is the same bytes as an on-disk DBF, so RAM↔disk snapshot
  ("materialize then convert to disk") is nearly free — no serialization impedance mismatch that
  most in-memory engines carry.
- **Self-ownership.** No kernel driver, no external service, no GPL/licensing exposure (the issue
  that retired the ImDisk RAM-disk route). For a redistributable product this outweighs raw
  benchmark wins.
  > Decision record: OS-level RAM disks were considered and rejected. On consumer Windows 10/11
  > there is **no native** RAM disk (a third-party signed driver — ImDisk/SoftPerfect/OSFMount —
  > is required; hence the license question). Windows **Server** *can* build one natively via the
  > built-in iSCSI Target (`New-IscsiVirtualDisk` on a `ramdisk:` path), and Linux has `tmpfs`.
  > All of these are **external OS block devices** (drive letter / mounted volume, reached through
  > the filesystem, DBF bytes marshaled across the OS boundary, admin/iSCSI setup). The in-process
  > VFS was chosen instead so RAM tables live in the engine's own address space — byte-identical
  > DBF, no driver, no drive letter, no admin, portable across Windows/Linux, trivial RAM↔disk
  > snapshot. The license concern was one input; the layer/self-ownership win is the durable one.
- **Latency for its workload.** RAM access, no syscalls, no fsync; ordered seek/range is
  O(log n) on the native index. Excellent for temp tables, index-build acceleration, ETL
  scratch, and deterministic test fixtures.

## 4. Limitations (honest, by design or by current milestone)

| Axis | RAM DBF (M1) | Why / scope |
|---|---|---|
| **Concurrency** | Single-process, single-thread; no MVCC, no locking. `reg()` registry is not internally locked (a mutex is a noted future milestone). | Deliberate M1 scope; multi-area sharing not yet a goal. |
| **Durability** | Ephemeral: RAM files dropped on unmount/exit. No in-RAM WAL. | By design — trades durability for speed. (Engine has WAL on the *disk* path; RAM↔disk snapshot is the opt-in durability lever.) |
| **Query model** | xBase navigational + expression predicates + REL joins + embedded SQLite. No cost-based SQL optimizer, no distributed/large-join planner. | Inherits the engine; not a planner rewrite. |
| **Analytics** | Row-oriented byte images; analytic scans read whole rows. | Architectural: row layout, not columnar/vectorized. OLAP-heavy work should use the embedded SQLite path or a future columnar projection. |
| **Data types** | DBF C/N/D/L/M + x64 I/B/Y/T. | No JSON/array/geo/full-text as first-class types. |
| **Scale** | One growable `std::vector<char>` per table, single address space, single cursor; grows with zero-fill. | Single-node, working-set-in-RAM; no buffer pool/eviction, no sharding. |
| **LMDB in RAM** | Out of scope — LMDB needs a real mmap'd file; stays a deferred symlink/RAM-disk add-on. | The native-CDX path is the M1 index because it is `ramfs`-routable. |

## 5. Head-to-head with the honest peer (SQLite `:memory:`)

| | RAM DBF | SQLite `:memory:` |
|---|---|---|
| Process model | In-process, single-thread | In-process, serialized single-writer |
| Query language | xBase command model + expressions + REL | Full SQL |
| Index | Native CDX-V64 (uint64 recno) B-tree | B-tree, SQL-defined |
| Persistence | Ephemeral; trivial byte-identical RAM↔disk DBF snapshot | Ephemeral; `.backup` to file DB |
| Maturity | New (M1), lane-scoped | Decades, ubiquitous |
| Differentiator | Engine transparency + DBF format fidelity + self-owned VFS | Full SQL + ecosystem maturity |

Net: you trade SQLite's full SQL and maturity for the xBase command model, native CDX fidelity,
and near-free RAM↔disk round-tripping. Neither dominates; they serve different runtimes.

## 6. Verdict

For its stated purpose the RAM DBF is a **strong, well-scoped design that punches above its line
count.** Its real differentiators — transparency, format fidelity, self-ownership — are exactly
what the large engines do not hand you cheaply. The only way to make it look weak is to grade it
against distributed OLTP or columnar OLAP systems, which are explicit non-goals.

## 7. Levers to close specific gaps (tied to backlog)

- **Ticket B** (typed tuple store) — memory density + typed access; a step toward columnar.
- **Concurrency milestone** — registry mutex + locking if/when multiple areas share the VFS.
- **RAM→disk snapshot** — opt-in durability using the existing byte-identical format.
- **OLAP path** — route analytical/aggregation-heavy queries through embedded SQLite (or a future
  columnar projection); do not try to make the row-image model do vectorized scans.

## 8. One-line summary for the lane

> The RAM DBF is a self-owned, in-process RAM substrate that makes the existing xBase engine —
> tables *and* native CDX-V64 index — run entirely in memory with full command transparency and
> trivial disk round-tripping. Its peer is SQLite `:memory:`, not SingleStore; its wins are
> transparency, format fidelity, and zero licensing exposure; its non-goals are concurrency,
> durability, SQL optimization, and analytical/distributed scale.
