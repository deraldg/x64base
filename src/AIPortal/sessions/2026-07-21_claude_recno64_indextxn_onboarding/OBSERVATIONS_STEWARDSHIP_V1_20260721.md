# Stewardship Observations — incidental issues spotted while reading source

**Date:** 2026-07-21 · **Author:** Claude (hosted AI), source-read only.
**Purpose:** things noticed **outside** the active lanes (XIDX-TXN / tuple-vectoring) while reading the code. Reported for your triage, not silently changed. Severity is my read; you own the call.

Legend: 🔴 correctness/data-loss · 🟠 robustness/perf · 🟡 maintainability · ✅ already addressed in a delivered drop.

---

## 🔴 O1 — Same LMDB env opened multiple times in-process (LMDB anti-pattern)
**Where:** `CdxBackend::open` (`src/xindex/cdx_backend.cpp`), `db_tuple_stream.cpp::collect_lmdb_cdx_recnos`, `order_nav.hpp::build_cdx_recnos_from_lmdb` / `cdx_endpoint_from_lmdb`, `cmd_buildlmdb.cpp` — each does its own `mdb_env_create`/`mdb_env_open` on the **same** `<cdx>.d` env.
**Why it matters:** LMDB explicitly warns not to open the same environment more than once in the same process (lock-table/reader-slot and corruption hazards). If a browse materialization (`db_tuple_stream`) or `order_nav` opens the env while `CdxBackend` already holds it open for the active order (or while a bulk write txn is open), that's the multiple-open case.
**Suggested action:** route all in-process LMDB access through a single cached env handle per container (e.g., own it in `IndexManager`/`CdxBackend` and lend RO txns), rather than each consumer opening its own. `cdx_cache_build` already prefers `cli::order_collect_recnos_asc` (the IndexManager-backed path) — extend that pattern to the other scanners.

## 🔴 O2 — RECNO32 truncation in ordered-nav (beyond the tuple layer)
**Where:** `order_nav.hpp`: `build_cdx_recnos_from_lmdb`, `cdx_endpoint_from_lmdb`, `cdx_cache_build` decode `uint64` then narrow to `uint32`/`int32`; range-check against `recCount()` (int32); `order_first_recno`/`order_last_recno` use `int32_t& out`; `order_stream_display` callback casts `uint64 recno → int32`.
**Why it matters:** x64 (DBF64) tables above `UINT32_MAX` records wrap/silently truncate in ordered TOP/BOTTOM/SKIP even after the tuple + stream layers are widened.
**Status:** catalogued as **Phase D** of `TUPLE_X64_VECTORING_RECNO64_V1`. Not yet delivered.

## 🟠 O3 — LMDB env open/close per navigation (perf)
**Where:** `db_tuple_stream.cpp::collect_lmdb_cdx_recnos` and `order_nav.hpp::build_cdx_recnos_from_lmdb` do a full `mdb_env_create`/`open`/`close` **every call**. ERSATZ re-materializes a fresh `DbTupleStream` per nav op (`ersatz_skip`/`ersatz_bottom`), so this is an env open+close **per keypress-level navigation**.
**Why it matters:** on large tables this is avoidable overhead (and compounds O1). A cached env + RO txn snapshot would make ordered browse/skip cheap.
**Suggested action:** same fix as O1 (shared env handle); also lets SKIP reuse the already-open ordered cursor instead of rebuilding the full recno vector.

## 🟡 O4 — Duplicated LMDB recno-scan logic (3 copies)
**Where:** `db_tuple_stream.cpp::collect_lmdb_cdx_recnos`, `order_nav.hpp::build_cdx_recnos_from_lmdb`, `order_nav.hpp::cdx_endpoint_from_lmdb` — three near-identical "open env → cursor scan → decode recno (8/4-byte LE or composite-key tail or ASCII)" implementations, each with its own `parse_recno`.
**Why it matters:** three places to fix for any encoding/format change (and O2's truncation had to be fixed in each). Divergence risk.
**Suggested action:** one shared `xindex`/`order` helper for "materialize ordered recnos for tag" and "first/last ordered recno", reused by tuple-stream, order_nav, and BUILDLMDB verification. `cli::order_collect_recnos_asc` may already be that primitive — consolidate onto it.

## 🟡 O5 — `orderstate::isCdx/isCnx` are filename-suffix checks, not live-backend checks
**Where:** `src/cli/order_state.cpp` — `isCdx`/`isCnx` test whether the tracked container path ends in `.cdx`/`.cnx`. They do **not** prove a live backend is attached.
**Why it matters:** a path can be set in orderstate without (or before) a live backend, so `orderstate::isCdx(A)` can disagree with `IndexManager::isCdx()` (the real `dynamic_cast<CdxBackend*>`). I used the live check for the COMMIT gate for exactly this reason; other call sites using `orderstate::isCdx` may carry the same latent mismatch.
**Suggested action:** audit `orderstate::isCdx/isCnx` call sites; where "is the transactional backend actually active" is meant, use `manager_if_attached(A)->isCdx()`.

## 🟡 O6 — `CnxDocument::save()` is a silent stub
**Where:** `src/cnx/cnx_document.cpp` — `save()` returns `false` with `"CnxDocument::save not implemented"`.
**Why it matters:** any caller that persists a CNX doc through `save()` silently no-ops (only the return value signals it). Fine today because the CNX write path is `rebuild()`, but it's a trap for future code. Tracked in lane `XIDX-TXN-02`.
**Suggested action:** either implement (lane XIDX-TXN-02 Phase A) or make the stub `assert`/log loudly so it can't be relied on unnoticed.

## 🟡 O7 — `on_replace` ordering vs `apply_replace_snapshot` ordering
**Where:** `include/xindex/index_manager.hpp` `on_replace` does `upsert(new)` **then** `erase(old)` (guarded by `old==new` early-return); `apply_replace_snapshot` does all `on_delete` **then** all `on_append`.
**Why it matters:** two different orderings for "replace." Safe today (composite `base‖recno8` keys make each entry unique, and the `old==new` guard prevents self-erase), but the inconsistency is a latent footgun if a UNIQUE (non-composite/DUPSORT) tag path is added later, where insert-then-delete of an equal key could erase the entry.
**Suggested action:** document the invariant, or unify on delete-old-then-insert-new.

## 🟡 O8 — `IOrderProvider` subsystem is DEAD CODE (resolved via caller audit)
**Where:** `include/cli/order_provider.hpp`, `src/cli/order_provider_default.{hpp,cpp}`, `include/cli/order_iterator_materialized.{hpp}` + `src/cli/order_iterator_materialized.cpp` (`DefaultOrderProvider`, `MaterializedOrderIterator`, `OrderPosition`, `IOrderIterator`, `OrderSpec`, `makeDefaultOrderProvider`, `buildActiveOrderSpec`).
**Evidence (GitHub code search, repo-scoped):** `makeDefaultOrderProvider` → **2 hits: def + decl only, no callers**. `buildActiveOrderSpec` → **2 hits: def + decl only, no callers**. `MaterializedOrderIterator` → 3 hits: its own header/impl + the dead `DefaultOrderProvider::createIterator`. The only factory is uncalled, so nothing constructs a provider; `materializeRecnos`/`createIterator`/`first/lastRecno` are unreachable.
**What the live surface actually uses:** the free-function order primitives in `include/cli/order_iterator.hpp` — `order_collect_recnos_asc`/`order_iterate_recnos`/`order_stream_display`/`order_step_cdx` (all `uint64` except `order_step_cdx`, see O9) — via `smartlist_query.cpp` (`order_iterate_recnos`), `order_nav.hpp`, and `db_tuple_stream.cpp` (its own `order_recnos_` vector, **not** `MaterializedOrderIterator`).
**Consequence for the vectoring work:** the original **Phase C (widen `IOrderProvider`/`OrderPosition`/`MaterializedOrderIterator`) is MOOT** — don't widen dead code. The stub `materializeCdx/Cnx` returning physical order is a latent trap only if someone wires the provider later.
**Suggested action:** delete the `IOrderProvider` subsystem (5 files) as dead code, or freeze it with a `// UNUSED — do not wire without implementing real CDX/CNX materialize` banner. Recommend delete; it removes O8 + the stub-order trap + shrinks Phase C to nothing. Your call.

## 🔴 O10 — `smartlist_query.cpp` narrows the ordered recno to int32
**Where:** `src/cli/smartlist_query.cpp::execute_query` — iterates via `order_iterate_recnos([&](uint64_t rn64){ … process_record(static_cast<int32_t>(rn64)); })`; `process_record(int32_t rn)` then calls `a.gotoRec(rn)` and uses `total = a.recCount()` (int32). It correctly guards `rn64 > recCount64()` but then **casts to int32** and navigates 32-bit.
**Why it matters:** SMARTLIST (the primary ordered listing surface) truncates recnos on x64 tables despite consuming the 64-bit primitive.
**Suggested action:** widen `process_record`/the consumer lambda to `std::int64_t`; use `gotoRec64`/`recCount64`. Fold into the RECNO64 package (same phase as `order_nav`/`order_step_cdx`).

## 🔴 O9 — `order_step_cdx(..., int32_t& out_recno)` truncates the CDX fast-path recno
**Where:** `include/cli/order_iterator.hpp` — the O(log n) ordered-SKIP primitive returns the landing recno as `int32_t&`. Its siblings `order_collect_recnos_asc`/`order_iterate_recnos`/`order_stream_display` already use `uint64_t` (good); `order_step_cdx` is the lone 32-bit hole in the *real* order interface. Caller `order_nav.hpp::order_skip` then compares against `recCount()` (int32).
**Why it matters:** on x64 tables the fast SKIP lands on a truncated recno. This is the one genuine interface truncation in the live order path (vs the stubbed provider in O8). It's the real Phase C/D target — much narrower than widening the whole `IOrderProvider`.
**Suggested action:** widen `order_step_cdx` out-param to `std::int64_t&` + its impl (`order_iterator.cpp`) + the `order_skip` caller, together. Fold into the RECNO64 Phase C/D package.

## 🔴 O11 — `CdxBackend` cursor decodes recno into `uint32` (root CDX truncation)
**Where:** `src/xindex/cdx_backend.cpp` — `decode_recno_from_cursor_key(bool, const MDB_val&, const MDB_val&, std::uint32_t& out)` decodes an 8-byte LE recno into `uint64 rec64` then `out = static_cast<std::uint32_t>(rec64)`. `LmdbCursor::first/next/last/prev` each declare `std::uint32_t r = 0;`, call it, then `outRec = static_cast<RecNo>(r)`. `RecNo = std::uint64_t` (`include/xindex/key_common.hpp`), so the value is truncated to 32 bits **before** being widened back to 64.
**Why it matters:** this is the **root** CDX recno truncation. `order_collect_recnos_asc` and `order_stream_display` walk this cursor (`IndexManager::scan()`), so every "64-bit" ordered CDX primitive silently loses the high 32 bits above `UINT32_MAX`. My Phase B fixed only the *raw*-LMDB scan in `db_tuple_stream::collect_lmdb_cdx_recnos`; the **cursor** path (used by SMARTLIST/SCAN/nav) still truncates until this is fixed. `stepOrdered` and `seekRecnoUserKey` already decode 64-bit — only the cursor path is affected.
**Exact fix (small, localized, `xindex.lib`):**
1. `decode_recno_from_cursor_key(..., std::uint32_t& out)` → `std::uint64_t& out`; both `out = static_cast<std::uint32_t>(rec64);` → `out = rec64;`.
2. In `LmdbCursor::first/next/last/prev` (4 spots) change `std::uint32_t r = 0;` → `std::uint64_t r = 0;` (or `xindex::RecNo r = 0;`). `outRec = static_cast<RecNo>(r)` then needs no cast.
Also `static inline bool decode_recno_from_cursor_key` at the top of the `#else`... n/a — it's `#if XINDEX_HAVE_LMDB` only. No other caller of that helper.
**Status:** delivered as `cdx_backend.recno64_cursor.EDITSPEC` (edit spec, since the 4 `r` locals are identical lines — hand-apply inside each method). This is the highest-value RECNO64 fix; recommend applying it first.

---

## Already addressed in delivered drops
- ✅ **collect_lmdb_cdx_recnos uint64→uint32 truncation** — fixed in `db_tuple_stream.cpp` (Phase B).
- ✅ **Commit gate used orderstate string** — M1 patch uses `ensure_manager(A).isCdx()` (live backend) — see O5 for the broader audit.
- ✅ **Browser/relation nav-cache staleness after transactional commit** — `orderhooks::reconcile_after_mutation(A)` folded into `cmd_commit.cpp`.

## Note
None of O1–O7 were changed outside their relevance to the active work. O1/O3 (shared LMDB env) is the one I'd rank worth scheduling on its own — it's a correctness hazard (O1) and a perf win (O3) with a single fix.
