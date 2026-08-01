# AI Change Package — Lane `XIDX-TXN-01` M1 Patch (LMDB index maintenance in COMMIT)

**File:** `AI_CHANGE_PACKAGE_LMDB_INDEX_TXN_MAINTENANCE_M1_PATCH_V1_20260721.md`
**Updates:** §4 of `AI_CHANGE_PACKAGE_LMDB_INDEX_TXN_MAINTENANCE_V1_20260721.md` (replaces the illustrative pseudocode with a concrete patch against real bodies).
**Status:** `review-needed` (source-evidenced proposal; not compiled/runtime-evidenced).
**Author:** Claude (hosted AI). Outside-AI Delivery Rule: reviewable package, no direct edits to `D:\code\ccode`.
**Durability contract:** D3 **option (a)** — `cdxmeta` guard + stale→`BUILDLMDB` reconciliation (per M0 addendum; ratification-pending, non-blocking).

---

## 1. Files touched

| File | Change |
|---|---|
| `src/cli/cmd_commit.cpp` | Bulk-txn lifecycle around the commit loop; per-record index edit via the `index_hooks` seam; `auto_reindex_if_needed` CDX message. |
| (none else) | `dbarea.cpp`, `cdx_backend.cpp`, `index_manager.*`, `attach.*`, `index_hooks.*` are **unchanged** — reused as-is. |

Rationale: the engine already routes index maintenance through `xbase::index_hooks::capture/apply_replace` (used by `DbArea::replaceFieldStored`) into the per-area `IndexManager` (`xindex::ensure_manager`). COMMIT's buffered path bypasses that seam by calling raw `set`+`writeCurrent`. M1 re-fires the same seam inside the commit loop, wrapped in one LMDB bulk txn so the edits are batched and atomic.

---

## 2. New includes (top of `cmd_commit.cpp`, guarded)

```cpp
#if DOTTALK_HAS_XINDEX
#include "xindex/attach.hpp"          // xindex::ensure_manager
#include "xindex/index_manager.hpp"   // IndexManager::{isCdx,beginBulkWrite,commitBulkWrite,abortBulkWrite}
#include "xbase/index_hooks.hpp"      // xbase::index_hooks::{capture,apply_replace}
#endif
```

---

## 3. `apply_one_recno` — fire the seam inside the existing lock

Add a `maintain_index` bool; capture the pre-image before the field writes and apply after. `A` is already positioned (`gotoRec64`+`readCurrent`) and record-locked in this function.

```cpp
static bool apply_one_recno(xbase::DbArea& A, const Agg& agg, bool talk,
                            bool maintain_index)          // NEW param
{
    const std::uint64_t rn = agg.recno;
    if (rn == 0 || rn > A.recCount64()) return false;
    if (!A.gotoRec64(rn)) return false;
    if (!A.readCurrent()) return false;

    std::string lock_err;
    if (!xbase::locks::try_lock_record(A, rn, &lock_err)) { /* unchanged */ return false; }

#if DOTTALK_HAS_XINDEX
    // Pre-image key snapshot (all field-backed tags) BEFORE mutating field bytes.
    xbase::index_hooks::Snapshot before;
    if (maintain_index) before = xbase::index_hooks::capture(A);
#endif

    bool ok = true;
    if (agg.flags & dottalk::table::CHANGE_UPDATE) {
        for (const auto& kv : agg.field_values) {
            if (!A.set(kv.first, kv.second)) { ok = false; break; }
        }
        if (ok) ok = A.writeCurrent();
    }
    if (ok && (agg.flags & dottalk::table::CHANGE_DELETE)) {
        ok = A.deleteCurrent();
    }

#if DOTTALK_HAS_XINDEX
    if (maintain_index && ok) {
        // DELETE (or update+delete) => erase keys: empty after-snapshot.
        // UPDATE only            => post-image after-snapshot (delete old / insert new).
        xbase::index_hooks::Snapshot after;
        if (!(agg.flags & dottalk::table::CHANGE_DELETE)) {
            (void)A.readCurrent();               // refresh to post-write bytes
            after = xbase::index_hooks::capture(A);
        }
        // Routes through IndexManager::apply_replace_snapshot -> CdxBackend::{erase,upsert};
        // with a bulk txn open these join it. Failure marks the edit for stale-reconcile.
        if (!xbase::index_hooks::apply_replace(A, before, after, rn)) {
            // Do not fail the DBF record for an index-apply miss; caller sets stale on commit.
            if (talk) cli::cmdout::print_prefixed_message(
                "COMMIT", dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText);
        }
    }
#endif

    xbase::locks::unlock_record(A, rn);
    return ok;
}
```

Semantics of `apply_replace(before, after, rn)` (existing, in `attach.cpp`): empty `after` ⇒ delete-only (erase all tag keys — correct for DELETE, which CDX excludes); both present ⇒ delete-old/insert-new per tag (unchanged tags net no-op). INSERT/APPEND is **not** materialized here (COMMIT does not handle `CHANGE_INSERT`) — see Open Q1.

---

## 4. `commit_one_area` — bulk lifecycle + disposition

Insert bulk open after `journal_begin_commit`, thread `maintain_index` into the loop, and dispose per the table in §5.

```cpp
static CommitResult commit_one_area(xbase::DbArea& A, int area0, bool talk, bool interactive_rebuild)
{
    auto& tb = dottalk::table::get_tb(area0);
    if (tb.empty()) { /* unchanged: NoChanges */ }

    CursorRestore restore(A);
    const auto pending_before = tb.changes;

    if (!dottalk::table::journal_begin_commit(area0)) { /* unchanged: FinalizeFailure */ }

    bool maintain_index = false;
#if DOTTALK_HAS_XINDEX
    auto& im = xindex::ensure_manager(A);
    // Gated by SET INDEXTXN (default OFF => legacy behavior; see
    // XIDX_INDEX_MAINTENANCE_FLAG_V1). Only the live CDX backend qualifies.
    maintain_index = cli::Settings::indexTxnOn() && im.isCdx();
    if (maintain_index) {
        std::string berr;
        if (!im.beginBulkWrite(&berr)) {            // open ONE rw MDB txn
            dottalk::table::set_dirty(area0, true);
            cli::cmdout::print_prefixed_message("COMMIT",
                dottalk::helpdata::MessageId::CommitIndexFinalizeFailedText, {{"detail", berr}});
            return {CommitStatus::FinalizeFailure, 0, 1};   // nothing applied yet
        }
    }
    // Helper: stale + rebuild is the D3(a) reconciliation net.
    auto index_abort_and_stale = [&](){
        if (maintain_index) { im.abortBulkWrite(); dottalk::table::set_stale(area0, true); }
    };
#else
    auto index_abort_and_stale = [](){};
#endif

    int applied_ok = 0, applied_fail = 0;
    for (auto it = tb.changes.begin(); it != tb.changes.end(); ) {
        const std::uint64_t recno = it->first;
        const auto range = tb.changes.equal_range(recno);
        const Agg agg = aggregate_for_recno(tb, recno);
        const bool ok = apply_one_recno(A, agg, talk, maintain_index);   // NEW arg
        if (ok) { ++applied_ok; it = tb.changes.erase(range.first, range.second); }
        else    { ++applied_fail; it = range.second; }
    }

    if (applied_fail != 0) {
        // Partial: applied records' DBF writes are durable and their buffer entries cleared,
        // so their index edits MUST persist to stay consistent -> commit the bulk.
#if DOTTALK_HAS_XINDEX
        if (maintain_index) {
            std::string cerr;
            if (!im.commitBulkWrite(&cerr)) dottalk::table::set_stale(area0, true);  // D3(a)
        }
#endif
        dottalk::table::set_dirty(area0, true);
        /* unchanged partial messaging */
        return {CommitStatus::PartialRecordFailure, applied_ok, applied_fail};
    }

    if (auto* mm = A.memoManagerPtr()) {
        std::string memo_err;
        if (!mm->flush(&memo_err)) {
            index_abort_and_stale();                 // retry redoes both (idempotent); stale = safety
            tb.changes = pending_before;
            dottalk::table::set_dirty(area0, true);
            /* unchanged memo-fail messaging */
            return {CommitStatus::FinalizeFailure, applied_ok, 1};
        }
    }

    dottalk::table::set_dirty(area0, false);
    if (!auto_reindex_if_needed(A, area0, talk, interactive_rebuild)) {  // CDX = maintained/skip
        index_abort_and_stale();
        tb.changes = pending_before;
        dottalk::table::set_dirty(area0, true);
        /* unchanged index-finalize messaging */
        return {CommitStatus::FinalizeFailure, applied_ok, 1};
    }

#if DOTTALK_HAS_XINDEX
    if (maintain_index) {                            // commit index BEFORE journal marker (D3)
        std::string cerr;
        if (!im.commitBulkWrite(&cerr)) {
            dottalk::table::set_stale(area0, true);  // DBF already applied; rebuild reconciles
            /* index-finalize messaging */
            return {CommitStatus::FinalizeFailure, applied_ok, 1};
        }
    }
#endif

    if (!dottalk::table::journal_note_commit(area0)) { /* unchanged FinalizeFailure */ }

    tb.clear();
    dottalk::table::set_dirty(area0, false);
    dottalk::table::set_stale(area0, false);
    dottalk::table::clear_stale_fields(area0);
    /* unchanged complete messaging */
    return {CommitStatus::Complete, applied_ok, 0};
}
```

`auto_reindex_if_needed`: in the `orderstate::isCdx` branch, change the user text from "skipped" to "maintained" (`CommitCdxSkippedText` → a new `CommitCdxMaintainedText`, or reuse with new wording). No control-flow change — CDX still returns `true` without rebuild.

---

## 5. Bulk disposition table (the contract)

| `commit_one_area` exit | DBF state | Bulk action | Area flag |
|---|---|---|---|
| `beginBulkWrite` fails | nothing applied | — (none open) | dirty; retry |
| Partial record failure | applied records durable | **commit** (persist applied edits) | dirty; stale iff bulk-commit fails |
| Memo flush fails | all applied, but commit retried | **abort** | dirty + **stale**; buffer restored (retry idempotent) |
| `auto_reindex_if_needed` fails (non-CDX branch) | all applied | **abort** | dirty + **stale**; buffer restored |
| `commitBulkWrite` fails | all applied | (already consumed) | **stale** (rebuild reconciles) |
| Success | all applied | **commit** before `journal_note_commit` | clean |

Invariant: **the LMDB index is committed exactly for the DBF writes that are durable and de-buffered.** Any residual DBF↔LMDB divergence (crash window between DBF flush and `commitBulkWrite`) is detectable via the `cdxmeta` guard and recovered by `BUILDLMDB` — D3(a).

---

## 6. Why no double-lock / no boundary break

- `apply_one_recno` already holds the record lock; we call the neutral `index_hooks` seam (not `replaceFieldStored`, which would re-lock).
- CLI names only `xbase::index_hooks::*` (neutral) and `IndexManager::{isCdx,begin/commit/abortBulkWrite}` (allowed at the composition layer per the Optional-Index Architecture Decision). `xbase` still names no index types.
- `index_hooks::apply_replace` → `manager_if_attached(A)` returns the **same** `IndexManager` on which `beginBulkWrite` opened `bulk_txn_`, so edits join that txn (confirmed: `ensure_manager` is the per-`DbArea` singleton; `apply_replace_hook` resolves the same instance).

---

## 7. Build / test (M1 → M2 proof)

- Build both toolchains (Windows/MSVC, WSL/Ubuntu), profiles `LMDB` and `NONE` (NONE must compile with the `#if` branches out and behave exactly as today).
- M2 regression (DotScript, add to `cmd_regression`):
  1. CDX order + `TABLE ON`; `REPLACE key WITH new`; `COMMIT`; `SEEK new` hits, `SEEK old` misses — **no** `BUILDLMDB` between.
  2. Multi-record buffered edits; force one locked record → `PartialRecordFailure`; verify applied records' keys are updated and the failed record's old key still resolves (its buffer entry retained).
  3. `ROLLBACK` after buffered edits → index unchanged (no bulk ever opened).
  4. DELETE a keyed record via buffer + `COMMIT` → `SEEK` no longer returns it (empty-after erase path).
  5. `NONE`/`LEGACY`(CNX) tables → unchanged behavior (CNX still rebuilds).

---

## 8. Open questions

- **Q1 (INSERT).** APPEND/`CHANGE_INSERT` is not materialized in `apply_one_recno`; new-record index insertion belongs in the append/commit path. Confirm the append flow and whether to fire `index_hooks` there under the same bulk txn (needs `beginBulkWrite` to span appends too). Scope for a follow-up, not this patch.
- **Q2 (message id).** Add `CommitCdxMaintainedText` or repurpose `CommitCdxSkippedText`. Needs a message-catalog entry.
- **Q3 (partial-commit policy).** This patch **commits** the bulk on partial record failure (index tracks durable DBF). If you prefer strict all-or-nothing, the alternative is abort+stale+rebuild on any partial — simpler but forces a rebuild after any single locked record. Recommend the commit-what-applied policy as written; flag for ratification.
- **Q4 (D3 ratification).** Confirm option (a) as the durability contract and the `commitBulkWrite`-before-`journal_note_commit` ordering.

---

## 9. Fallback

Every `#if DOTTALK_HAS_XINDEX` block is additive and gated on `im.isCdx()`. Compiling it out (or a table without a live CDX backend) yields today's exact behavior. If M2 fails, disable the bulk wrap; the area's stale flag + `BUILDLMDB` restore correctness with no format change.
