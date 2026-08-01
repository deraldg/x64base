# Consideration — Relations & Joins vs. Transactional Index Maintenance

**Date:** 2026-07-21 · Applies to lanes `XIDX-TXN-01` (LMDB) and `XIDX-TXN-02` (CNX).
**Author:** Claude (hosted AI), source-read.
**Bottom line:** relations and joins are **consumers** of the index (they SEEK it to position child rows). Transactional maintenance makes their results correct **after a key mutation without a rebuild** — a net improvement. One caveat: read-your-own-writes if a relation/join SEEK ever runs *inside* an open COMMIT bulk txn.

---

## 1. How relations/joins use the index

- `SET RELATION ... INTO <child> ON <keyexpr>` and `SET RELATIONS ADD parent child ON key` position the child by SEEK-ing the child's active order on the relation key (`rel_enum_engine`, `rel_iter`, `join_engine`, `ersatz`).
- So a child row is only reachable through a relation/join if its key is present and correct in the child's index.

## 2. Effect of the lane (flag ON) — mostly positive

- **Today (flag OFF / pre-M1):** mutate a child's key field, `COMMIT` → child index is stale until `BUILDLMDB`/`REBUILD`. A relation/join SEEK on that key **misses or mispositions** until the rebuild. This is a latent correctness gap for relation-driven browses after edits.
- **Flag ON (M1):** the child's index is maintained inside `COMMIT`, so the very next relation/join traversal finds the new key — correct with no rebuild. **The lane closes a relation/join staleness gap.**
- **Duplicates:** relations that fan out to multiple child rows sharing a key rely on all duplicates being present. The composite `base‖recno8` encoding preserves every duplicate; incremental `erase`/`upsert` touch only the mutated row's entry, so sibling duplicates in a relation set are undisturbed (confirmed design; demonstrated by `SEEK WHITE` still finding rec 54 after rec 12's edit).

## 3. Caveat — read-your-own-writes within COMMIT

- While a bulk txn is open during `COMMIT`, `CdxBackend` reads (`seek`/`scan`) use a fresh `MDB_RDONLY` txn → LMDB MVCC shows the *last committed* snapshot, **not** the pending bulk edits.
- **Current risk: none in the commit loop** — `commit_one_area` does not traverse relations or fire joins per record; it only writes records. Relation/join SEEKs happen during navigation/browse, *after* `commitBulkWrite()`, so they see the committed new state.
- **Becomes relevant if** a future per-record commit hook (trigger, RULE, relation refresh, VALIDATE UNIQUE) SEEKs the index mid-commit. Then apply the deferred **borrow-txn fix** (M1 patch §4.4): route reads through `bulk_txn_` when `inBulk()`. Tracked, not needed for the current commit path.

## 4. M2 test dimension to add (relations/joins)

Extend the proof (mirror `dottalkpp/data/scripts/stable_demo.dts` / `rel_join_enum_regression.dts`):

1. Open parent + child on a disposable copy; `SET RELATION`/`SET RELATIONS ADD ... ON <key>` where the child is ordered (CDX/LMDB) by that key.
2. `SET INDEXTXN ON`; buffered `REPLACE <child key> WITH <sentinel>`; `COMMIT`.
3. Traverse the relation from the parent whose key now maps to the sentinel → **EXPECT (post-M1): related child row resolves via the new key**, with **no** `BUILDLMDB`/`REBUILD`.
4. Duplicate fan-out: a parent key matching several child rows still returns all of them after one sibling's unrelated edit.
5. Negative control with `SET INDEXTXN OFF` → relation SEEK on the new key misses until rebuild (documents the gap the flag closes).

## 5. SmartBrowser + REL findings (source-read)

- **`cmd_SMART_BROWSER`** drives `dottalk::DbTupleStream` with an **ordered** mode (`is_ordered()`, `goto_pos()` vs `goto_recno()`) and reads relation children via `relations_api::{refresh_if_enabled, preview_child}` + `relations_status::relation_stats_for_current_parent`. On exit it restores cursors and calls `relations_api::refresh_if_enabled()`.
- **`cmd_REL`** dispatches `JOIN`/`ENUM` into `cmd_REL_JOIN`/`cmd_REL_ENUM` (relation engine) and `ADD`/`CLEAR` into `SET RELATIONS`.
- There is an **`order_iterator_materialized`** path and a relations **refresh** step — a cache layer distinct from the index backend.
- **`orderhooks::reconcile_after_mutation(area)`** already exists and calls `order_nav_invalidate(area)` (+ re-picks the CDX/CNX active tag). But **buffered `COMMIT` does not call it** — `apply_one_recno` writes via raw `set`/`writeCurrent`, bypassing the CLI mutation hooks.

### Consequence
`SEEK` (via `cmd_seek` → `CdxBackend`) reads the **live** backend, so the M2 gate flips correctly. But a **SmartBrowser ordered page** or **relation match cache** built on the materialized order / nav cache can lag after a transactional `COMMIT`, because the nav cache was not invalidated.

### M1 scope addition (defensive)
In the transactional commit path (flag ON), after a successful area commit, call `orderhooks::reconcile_after_mutation(A)` (or at least `order_nav_invalidate(A)`) once per committed area so the browser's ordered traversal and relation enum reflect the maintained index. This mirrors what the immediate/`replaceFieldStored` mutation path already triggers at the CLI layer. Cheap, and it closes the browser/relation staleness window without touching the backend.

### RJ3 RESOLVED — ordered nav materializes from the live index
`cmd_ersatz.cpp` (navigation core) and `cmd_smart_browser.cpp` both traverse ordered data through `dottalk::DbTupleStream`, which — per its own comment — *"already knows how to materialize CNX/CDX/INX record vectors and honor ASC/DESC."* So:
- Ordered TOP/BOTTOM/SKIP build a **materialized ordered recno vector from the live index backend** (CDX/LMDB scan, CNX RUN1, INX) — the same backend this lane maintains. `rel_enum_engine::run` delegates child matching to `relations_api::enum_emit_for_current_parent` and per-hop counts to `relations_api::list_tree_for_current_parent` (relation state, refreshed via `refresh_if_enabled`).
- **ERSATZ re-materializes per nav op** (each `ersatz_skip`/`ersatz_bottom` constructs a fresh `DbTupleStream`), so it always reflects the current index — post-M1 edits show immediately.
- **SmartBrowser holds one stream per paging session**; it re-materializes on `TOP`/`SPEC`. A commit mid-session (atypical — the browser is read-only) would need a `TOP`/refresh to re-materialize.

**Net:** because materialization reads the maintained backend, incremental maintenance is consumed correctly on the next materialization. The §5 `reconcile_after_mutation`/`order_nav_invalidate` call is therefore **defensive** (covers long-lived streams + nav caches), not required for a fresh materialization's correctness. Pre-M1, the same materialization would inherit the *stale* index — so the lane fixes browser/relation ordered views too.

## 6. Open questions

- **RJ1.** Enumerate the commit-time call sites (if any) that SEEK the index: trigger/RULE firing, relation auto-refresh, VALIDATE UNIQUE. If any run inside `COMMIT`, promote the borrow-txn fix from deferred to M1-required. (Prior D2 finding: none in `commit_one_area` today.)
- **RJ2.** Cross-area `COMMIT ALL` with a relation spanning two areas both being committed: confirm each area's independent bulk commit + read-time relations yield a consistent view (expected fine, since relations read post-commit).
- **RJ3 (RESOLVED — see §5).** `MaterializedOrderIterator` (read) is a plain `std::vector<uint32_t> recnos_` snapshot walked by top/next/prev — built from the index at materialization time. `DbTupleStream` constructs it from the active order (CDX/LMDB/CNX/INX). ERSATZ re-materializes per nav (always current). The commit-time `orderhooks::reconcile_after_mutation(A)` (now folded into `cmd_commit.cpp`) drops nav/order caches so the next materialization rebuilds from the maintained backend — covering the only staleness window (a long-lived stream). Only residual, optional: confirm in `db_tuple_stream.cpp` that the vector is built via `CdxBackend::scan` (expected) vs a separately cached order.
- **RJ4.** Does the transactional `COMMIT` need to call `relations_api::refresh_if_enabled()` as well, so open relation sets re-sync to maintained child keys immediately (not only on the next browser exit / REL REFRESH)?
