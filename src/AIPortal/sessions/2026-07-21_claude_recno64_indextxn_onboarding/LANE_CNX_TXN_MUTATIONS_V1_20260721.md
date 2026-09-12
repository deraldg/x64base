# LANE — CNX (Native) Transactional Mutations

**Lane code:** `XIDX-TXN-02`
**Lane name:** CNX native-format transactional index mutation (no LMDB)
**Status:** `planned lane`  *(not earned: no source landed, no runtime evidence)*
**Owner:** Derald (engine) · drafting partner: Claude (hosted AI, change-package delivery only)
**Created:** 2026-07-21
**Sibling lane:** `XIDX-TXN-01` (LMDB lane) — shares the COMMIT wrap + `index_hooks` seam; differs entirely in the backend write path.

> **Authority hierarchy.** Conventions suggest. Registration declares. Metadata records. Runtime proves. Validators enforce. This file *declares* the lane; status is earned per gate by proof artifacts.

---

## 1. One-line

Give the **native** CNX lane a real transactional mutation path so an indexed key change no longer forces a full DBF re-scan rebuild — without introducing an LMDB dependency (CNX stays the LMDB-free / `LEGACY`-profile lane).

## 2. Why a lane (and why it is *not* the LMDB lane)

Confirmed from source:

- `CnxBackend::upsert` / `erase` are **no-ops** — they only set `stale_ = true` ("CNX does not incrementally maintain on mutation in v1").
- The only maintainer is `CnxBackend::rebuild()`: full `collect_sorted_recnos_for_tag_` DBF re-scan → re-sort → rewrite `RUN1` blocks + tag directory.
- `CnxDocument::save()` is a **stub** ("not implemented").
- On-disk form is `RUN1`: a flat run of **uint32** record numbers (materialized sorted list), V32 lane. `include/cnx/cnx.hpp` reserves `TagDirEntry.root_page_off` for "future B-tree pages" and defines `CNX_HDRF_DIRTY` — the format already anticipates a mutable tree and a dirty marker.
- The `xbase::index_hooks` seam **does** fire for CNX (via `apply_replace_snapshot` → `on_delete`/`on_append`), but lands on the no-op backend. So the wiring exists; the CNX write implementation does not.
- COMMIT already routes CNX through `cmd_REBUILD` in `auto_reindex_if_needed`.

Unlike `XIDX-TXN-01`, CNX has **no mutable tree and no external transactional KV store** to lean on. Transactional mutation must be built into the native format itself. This lane is the direct execution of the Optional-Index Architecture Decision's "remaining proof item 1: attached-CNX replace/append/delete/recall/pack synchronization."

## 3. Approach options (decide at M0)

- **Option A — in-memory delta + atomic commit rewrite (near-term).** During a transaction, apply key deltas to the loaded in-memory ordered payload (`InxPayload`); on COMMIT, implement `CnxDocument::save()` to write a fresh, consistent `.cnx` to a temp file, fsync, and atomically rename over the original (set/clear `CNX_HDRF_DIRTY` around the swap). ROLLBACK discards the in-memory delta. **Transactional & crash-atomic at the file level; still O(n) file write**, but removes the O(n·log n) DBF re-scan+re-sort and is a small, self-contained build.
- **Option B — reserved B-tree pages (target).** Implement the paged B-tree the header already reserves (`root_page_off`, `CNX_DEFAULT_PAGE_SIZE`, page allocator + free list), making `upsert`/`erase` real O(log n) page ops with copy-on-write root swap or a page journal for atomicity. True native incremental maintenance; larger build.
- **Option C — status quo (baseline).** Keep rebuild-on-commit; route transactional workloads to the LMDB lane. Honest fallback if A/B are deferred.

**Recommended path:** A for v1 (earns transactional correctness + atomic persistence cheaply), then B for incremental performance. C remains the documented fallback.

> **C1 RULED (owner, member.derald, 2026-07-30): Option A AND Option B, in that order.**
> A ships first as the v1 transactional path; B is the committed target, not a maybe.
> C stays only as the torn-write recovery behavior (dirty flag -> rebuild), never as a
> destination. Same doctrine as the SQL lane's R29 ("measure twice, cut once"): build A
> shaped so B is an EXTENSION, not a rewrite. Concretely, A must:
>   1. keep the transaction delta as its OWN ordered structure ({op, key, recno} list),
>      never smeared into InxPayload -- B consumes the same delta as page operations;
>   2. implement save() = temp file + fsync + atomic rename + CNX_HDRF_DIRTY lifecycle
>      ONCE -- B reuses the identical dirty-flag/torn-write contract (C3 answered here);
>   3. leave upsert()/erase() as the only mutation entry points; the index_hooks seam
>      does not change between A and B;
>   4. enforce the C2 uint32 capacity guard in A -- B inherits it unchanged;
>   5. gate COMMIT per C4 (delta-apply+save fast path, full rebuild() fallback) -- B
>      swaps only the apply/persist internals inside that gating.
> Net: A builds four of the five things B needs; B replaces one. Mark each seam with a
> greppable `B-READY:` comment so the B work list is one grep, not archaeology.

## 4. Scope

**In:** `cnx_backend.cpp` (`upsert`/`erase` real implementation or in-mem delta), `cnx_document.cpp` (`save()` implementation, atomic swap, dirty-flag lifecycle), COMMIT wiring so CNX uses delta-apply+save instead of unconditional `cmd_REBUILD`, `cnx.hpp` page structures if Option B.
**Out:** LMDB lane (`XIDX-TXN-01`), INX/IDX, the DBF engine seam (`index_hooks` already fires for CNX — reused unchanged).

## 5. Dependencies / preconditions (answer before M1 exit)

- **C1** — Approach decision A vs B vs C (§3).
- **C2** — V32 capacity policy: CNX recnos are uint32; define behavior when a table exceeds the 32-bit ceiling (reject via `recordNumberFitsBackend`, or promote to LMDB/V64). Confirm `backendMaxRecordNumber()` for `CnxBackend`.
- **C3** — Atomicity model for the `.cnx` swap (shares LMDB lane D3 spirit): temp-file + fsync + rename + `CNX_HDRF_DIRTY` detection on open → rebuild fallback on torn write. Confirm rename atomicity on the Windows/MSVC target.
- **C4** — COMMIT contract change: `auto_reindex_if_needed` currently calls `cmd_REBUILD` for CNX unconditionally. Decide gating: delta-apply+save on the fast path, fall back to full `rebuild()` when the in-memory payload is absent/stale or the delta is unbounded.
- **C5** — Buffered-vs-immediate parity: `TABLE OFF` REPLACE fires the seam onto the CNX no-op today (marks stale). Define whether immediate CNX edits apply-in-place+save per edit (autocommit) or defer to an explicit COMMIT/REBUILD.

## 6. Milestone gates (falsifiable exit conditions + proof)

### M0 — Discovery / approach locked  → readiness `source-evidenced`
**Exit:** C1–C5 answered; `RUN1`/tagdir/reserved-B-tree layout and `save()` contract fully specified; edit sites anchored in `cnx_backend.cpp` / `cnx_document.cpp` / `cmd_commit.cpp`.
**Proof:** M0 findings note appended to this lane.

### M1 — Transactional persistence landed (Option A)  → `source-evidenced`
**Exit:** `CnxDocument::save()` implemented with atomic temp+fsync+rename and dirty-flag lifecycle; COMMIT applies buffered key deltas to the in-memory payload then `save()`s (no full DBF re-scan on the fast path); ROLLBACK discards delta. Compiles on Windows/MSVC + WSL/Ubuntu.
**Proof:** build logs (both toolchains) + reviewed diff manifest + `git` sha.

### M2 — Correctness + crash-atomicity proven  → `runtime-evidenced` (candidate `active beta`)
**Exit (no full rebuild between steps):**
1. `SET ORDER` (CNX); `TABLE ON`; `REPLACE key WITH new`; `COMMIT`; `SEEK new` hits, `SEEK old` misses.
2. Kill the process mid-`save()` (or simulate torn rename) → reopen detects `CNX_HDRF_DIRTY` → falls back to `rebuild()` and `SEEK` is correct (no silent corruption).
3. `ROLLBACK` after buffered CNX key edits → `.cnx` unchanged, `SEEK old` still hits.
4. Regression vs LMDB lane: same script on a CNX table and a CDX/LMDB table yields identical SEEK results.
**Proof:** DotScript regression added to `cmd_regression`; captured transcript + before/after `.cnx` byte-diff/fixture hashes.

### M3 — Native incremental (Option B) + capacity  → `active beta`
**Exit:** reserved B-tree pages implemented; `upsert`/`erase` O(log n) with atomic root swap or page journal; V32 capacity policy (C2) enforced with a clear error; perf artifact shows key REPLACE+COMMIT drops from rebuild-class to sub-linear on a large table.
**Proof:** perf report `labtalk/reports/selfdoc/cnx_txn_bench_v1.md`; capacity-rejection test.

## 7. Status ledger

| Date | Gate | Status | Evidence |
|---|---|---|---|
| 2026-07-21 | — | `planned lane` | This declaration (source-read only) |
| 2026-07-21 | M0 | **met** — C1–C5 settled; approach **A** (in-mem delta + atomic `save()`), format-neutral; M2 reshaped | `LANE_XIDX_TXN_02_M0_FINDINGS_V1_20260721.md` |
| | M1 | **ready** — implement `CnxDocument::save()` + in-mem `upsert/erase` + C4 COMMIT branch | |
| | M2 | pending (reshaped: regression-retention + crash-atomicity + perf, **not** a correctness flip) | |
| | M3 | pending | |

> **Maintenance-mode flag (`SET INDEXTXN`, default OFF):** the transactional delta+`save()` path is gated by the same flag as the LMDB lane. OFF ⇒ `cmd_REBUILD`-on-commit (today's behavior, permanent). ON ⇒ in-mem delta + atomic `save()` with rebuild fallback. The CNX correctness guard must pass in **both** states. See `XIDX_INDEX_MAINTENANCE_FLAG_V1_20260721.md`.

> **M0 reshaping finding:** CNX correctness is **already** satisfied by `cmd_REBUILD`-on-commit (`auto_reindex_if_needed`). This lane replaces that full re-scan with in-memory delta + atomic `CnxDocument::save()`; its proof is *retain correctness + crash-atomic swap + no full re-scan (perf)*, not a red→green SEEK flip. C2: `CnxBackend::maxRecordNumber()==UINT32_MAX` (V32 ceiling) — gate `recordNumberFitsBackend` exists, enforce at call sites. See M0 findings.

## 8. Risks / watch items

- **Format lock-in:** Option A rewrites `RUN1`; Option B introduces pages. Decide the on-disk versioning story (bump `CNX_VERSION`) so old readers reject/upgrade cleanly.
- **Atomic rename on Windows:** confirm `ReplaceFile`/rename-over semantics; a non-atomic swap defeats crash-safety — the `CNX_HDRF_DIRTY` guard is the backstop.
- **V32 ceiling:** uint32 recnos cap the addressable table; must fail loud, not truncate (C2).
- **Delta unboundedness:** a commit touching most rows makes "delta + rewrite" no cheaper than rebuild; C4 fast-path gating must fall back gracefully.
- **Collation parity:** `collect_sorted_recnos_for_tag_` sort order must match SEEK collation (open concern already noted for CDX) — verify for CNX character/numeric/date kinds.

## 9. Fallback

Additive and gated on `isCnx`. If M1/M2 fail, revert to today's `cmd_REBUILD`-on-commit (Option C) with no format change. Lane returns to `planned lane`.

## 10. Register

- Lane code `XIDX-TXN-02` — reserve in the lane registry.
- Family: `XIDX-TXN-01` (LMDB lane, default), `XIDX-TXN-02` (this, native CNX). Shared infra: COMMIT bulk boundary pattern, `index_hooks` seam, status/proof conventions.
- Realizes Optional-Index Architecture Decision "remaining proof item 1" (attached-CNX mutation synchronization).

### 10.1 Native format twin finding (`XIDX_NATIVE_FORMAT_FINDINGS_V1_20260721.md`)

Native CNX (`cnxfile::`) and native CDX (`cdxfile::`) are **structurally identical container formats** — same header, `TagDirEntry`, `TableBind`, API, and raw RUN/page primitives — differing only in magic (`"CNX1"` vs `"CDX1"`) and recno width (V32 uint32 vs V64 uint64). CNX has a **working** native key path (`CnxDocument` RUN1); native CDX's key path is **absent** (used as tagdir-only; LMDB fills the role).

**Design directive for this lane:** author the mutable/transactional native write path (Option A RUN rewrite or Option B reserved B-tree pages) **format-neutrally** — against `append_bytes`/`read_at`/`write_at`, `root_page_off`, `*_HDRF_DIRTY`, parameterized by magic + recno width — so it serves both `.cnx` (V32) and a future `.cdx` (V64) native store. Consider unifying `cnxfile::`/`cdxfile::` behind one implementation.

- New candidate follow-up lane **`XIDX-NATIVE-CDX-01`** (native CDX V64 key path, no LMDB) — deferred; unlocked "almost for free" if `XIDX-TXN-02` is authored format-neutrally.
