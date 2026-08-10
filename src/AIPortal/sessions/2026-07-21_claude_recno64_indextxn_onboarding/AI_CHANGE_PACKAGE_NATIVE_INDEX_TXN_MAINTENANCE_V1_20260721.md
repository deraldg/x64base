# AI Change Package — Native (CDX/LMDB) In-Transaction Index Key Maintenance

**File:** `AI_CHANGE_PACKAGE_NATIVE_INDEX_TXN_MAINTENANCE_V1_20260721.md`
**Status:** `review-needed` (draft proposal — *source-evidenced*, not yet *runtime-evidenced*)
**Author:** Claude (hosted AI). Delivered under the Outside-AI Delivery Rule: this is a reviewable package, no direct edits to `D:\code\ccode`.
**Scope:** Wire the existing `IndexManager` snapshot/bulk API into the COMMIT path so **native index** keys are maintained incrementally inside one LMDB transaction, replacing full rebuild on key mutation. CNX unchanged.

> **Terminology.** *Native indexing* = the CDX front-end organizer running over the LMDB backend (`CdxBackend` + `LmdbBackend`, the V64 lane). Distinct from the CNX self-contained `.cnx` file lane (V32), which has no mutable tree. "Native index" is used throughout this document for the CDX/LMDB scheme. *(Flagged for possible follow-up: standardizing this term across HELP/manualgen and the crosswalk.)*

---

## 1. Intent

Today an indexed key `REPLACE` on the native lane does not update the index; correctness is currently recovered by a full rebuild. The engine already has:

- per-key ops: `CdxBackend::upsert` (`mdb_put`), `CdxBackend::erase` (`mdb_del`);
- one-transaction batching: `beginBulk`/`commitBulk`/`abortBulk` (surfaced as `IndexManager::beginBulkWrite`/`commitBulkWrite`/`abortBulkWrite`);
- snapshot helpers: `capture_delete_snapshot_for_current_record`, `apply_replace_snapshot`, `apply_delete_snapshot`, `apply_insert_snapshot`.

This package connects those to `COMMIT`, aligned to the existing record-lock + write-ahead-journal critical section, so native index and data commit/roll back together.

---

## 2. Contracts read

| File | Guarantee relied on |
|---|---|
| `src/cli/cmd_commit.cpp` | `commit_one_area` locks each recno via `xbase::locks::try_lock_record`, applies buffered field writes, then `auto_reindex_if_needed`; write-ahead `journal_begin_commit` runs before DBF apply; buffer restored (`tb.changes = pending_before`) on finalize failure. `auto_reindex_if_needed` **skips the native (CDX/LMDB) lane** by contract. |
| `src/cli/cmd_replace.cpp` | `TABLE ON` buffers into `tb.add_change(...)`, no index call, no lock. `TABLE OFF` writes immediately via `replaceFieldStored`, marks stale, no index call. |
| `src/cli/cmd_rollback.cpp` | `rollback_area` clears the buffer + dirty/stale flags; `journal_note_rollback`. No data or index mutation. |
| `include/xindex/index_manager.hpp` | `capture_delete_snapshot_for_current_record` (native lane walks all field-backed tags), `apply_replace_snapshot(before, after, rec)` (delete-all-before then insert-all-after), bulk API is native-lane-only, no-op/false otherwise. |
| `src/xindex/cdx_backend.cpp` | While `bulk_txn_` is open, `upsert`/`erase`/`setTag` route onto the shared txn. `seek`/`scan`/`seekRecnoUserKey`/`stepOrdered` open a **separate** `MDB_RDONLY` txn (do **not** see bulk-pending writes). DBI storage mode derived per-call from live flags (composite key `base‖recno8` vs DUPSORT dup value). |
| `src/cnx/cnx_backend.cpp` | `upsert`/`erase` are no-ops (`stale_=true`); only `rebuild()` maintains. Unchanged by this package. |

---

## 3. As-is behavior (evidence)

1. `REPLACE key_field` (`TABLE ON`) → buffered only; index untouched; area marked stale.
2. `COMMIT` → applies field writes under per-record lock; `auto_reindex_if_needed` prints `CdxSkipped` and returns `true` for the native lane → **index never updated at commit**.
3. Net: the native index is stale after any key mutation until an out-of-band rebuild/`BUILDLMDB`. This is the behavior being replaced.

---

## 4. Proposed call sequence

### 4.1 COMMIT (buffered path) — native lane only

Insert an index-maintenance wrapper into `commit_one_area`, gated on `orderstate::isCdx(A)`:

```
commit_one_area(A, area0):
    tb = get_tb(area0); if tb.empty(): return NoChanges
    restore = CursorRestore(A)
    pending_before = tb.changes

    if !journal_begin_commit(area0): return FinalizeFailure   # unchanged (WAL first)

    native = isCdx(A)                                         # NEW
    if native:                                                # NEW
        if !im.beginBulkWrite(&err): abort→FinalizeFailure    # opens ONE MDB rw txn

    for each recno in tb.changes:
        agg = aggregate_for_recno(tb, recno)
        gotoRec64(recno); readCurrent()
        if !try_lock_record(A, recno): mark fail; continue    # use-based lock (unchanged)

        # --- NEW: pre-image key snapshot (old keys), native only ---
        before = native ? im.capture_delete_snapshot_for_current_record() : {}

        ok = apply_field_writes(agg)  # A.set + writeCurrent, delete flag  (unchanged)

        # --- NEW: post-image key snapshot + apply onto bulk txn ---
        if ok and native:
            if   agg.flags & CHANGE_DELETE:
                     im.apply_delete_snapshot(before, recno)
            elif agg.flags & CHANGE_INSERT:
                     readCurrent(); after = im.capture_delete_snapshot_for_current_record()
                     im.apply_insert_snapshot(after, recno)
            else:  # CHANGE_UPDATE
                     readCurrent(); after = im.capture_delete_snapshot_for_current_record()
                     im.apply_replace_snapshot(before, after, recno)

        unlock_record(A, recno)                                # unchanged
        record ok/fail exactly as today

    if applied_fail != 0:
        if native: im.abortBulkWrite()                         # NEW: drop all index edits
        set_dirty(area0,true); return PartialRecordFailure     # buffer retained (unchanged)

    if memo flush fails:
        if native: im.abortBulkWrite()                         # NEW
        tb.changes = pending_before; return FinalizeFailure    # unchanged otherwise

    # auto_reindex_if_needed stays a SKIP for the native lane (now truthfully
    # "maintained"), still REBUILD for CNX, REINDEX for INX/IDX.  (message change only)
    if !auto_reindex_if_needed(...):
        if native: im.abortBulkWrite()                         # NEW
        tb.changes = pending_before; return FinalizeFailure

    if native:                                                 # NEW: commit index with data
        if !im.commitBulkWrite(&err):
            tb.changes = pending_before; return FinalizeFailure

    if !journal_note_commit(area0):
        # NOTE: index bulk already committed above; see Open Question Q3 on ordering
        tb.changes = pending_before; return FinalizeFailure

    tb.clear(); clear dirty/stale; return Complete
```

Key ordering choices:

- **Pre-image capture must precede the field write** (old key = on-disk value); post-image after `writeCurrent()`.
- **Bulk commit is placed after `auto_reindex_if_needed` and before `journal_note_commit`** so a reindex/finalize failure still aborts the index txn. See Q3 for the residual data/index atomicity window.
- `apply_replace_snapshot` uses delete-before-then-insert-after ordering; unchanged tags yield equal before/after entries (delete+reinsert of the same `(key,recno8)` = net no-op), so it is safe but slightly wasteful — see 4.5 optimization.

### 4.2 ROLLBACK — no change required

Because index writes now happen **only** inside the COMMIT bulk txn, an un-committed transaction never touched the index. `rollback_area` stays index-neutral. If `COMMIT` aborted mid-way, `abortBulkWrite()` already discarded the LMDB txn. **Recommendation: keep native index maintenance strictly commit-time** precisely to preserve this property.

### 4.3 REPLACE with `TABLE OFF` (immediate)

No enclosing transaction exists, so autocommit each edit. After `replaceFieldStored` succeeds and if `isCdx`:

```
im.replace_active_field_value(field1, before, after, recno)  # on_replace: upsert(new) then erase(old), guarded old==new
```

`replace_active_field_value` (no open bulk) uses the per-op autocommit path — one `mdb_txn` per edit. Acceptable in `TABLE OFF` mode, which has no rollback expectation.

### 4.4 Read-your-own-writes fix (needed if any mid-commit index read exists)

Problem: while `bulk_txn_` is open, `CdxBackend::seek`/`scan`/`seekRecnoUserKey`/`stepOrdered` call `ensure_ro_txn_()` (fresh `MDB_RDONLY`), which under LMDB MVCC sees the last *committed* snapshot — not pending bulk edits. A `VALIDATE UNIQUE` or trigger seek during commit would miss the new key.

**Fix (borrow the bulk txn for reads):** when `inBulk()`, open read cursors on `bulk_txn_` instead of a new RO txn.

```
MDB_txn* CdxBackend::read_txn_() const:
    return bulk_txn_ ? bulk_txn_ : ensure_ro_txn_();
```

- `seek`/`scan`/`seekRecnoUserKey`/`stepOrdered`: replace `ensure_ro_txn_()` with `read_txn_()`.
- `LmdbCursor` must **borrow, not own**, a bulk txn: add `bool owns_txn_`. In the destructor `mdb_txn_abort(txn_)` only when `owns_txn_` (i.e., the RO case). Never abort/commit `bulk_txn_` from a cursor.
- Cursor lifetime must not outlive the bulk txn (it won't within a single commit critical section).

If no index read occurs during commit (see Q1), the alternative is "do nothing extra" — commit reads only happen after `commitBulkWrite()`. Recommended default: **implement the borrow-txn fix**, because it is the correctness precondition for enforcing UNIQUE at commit.

### 4.5 Optimization (optional)

Limit snapshots to tags whose field actually changed: build `before`/`after` only for `field1 ∈ agg.field_values` (map field→tag via `activeTagFieldIndex1`). Avoids delete+reinsert churn on unchanged tags. Correctness holds without it; this is throughput only.

---

## 5. Patch surface (illustrative)

- `src/cli/cmd_commit.cpp` — add bulk wrap + per-recno pre/post snapshot calls in `commit_one_area`; adjust `auto_reindex_if_needed` native branch message from "skipped" to "maintained".
- `src/cli/cmd_replace.cpp` — `TABLE OFF` path: add `replace_active_field_value` after successful `replaceFieldStored` (native only).
- `src/xindex/cdx_backend.cpp` — add `read_txn_()`; route read paths through it; add `owns_txn_` to `LmdbCursor`.
- `include/xindex/cdx_backend.hpp` — declare `read_txn_()`, `owns_txn_` (header not yet read — confirm member layout).
- No change: `cmd_rollback.cpp`, `cnx_backend.cpp`, `lmdb_backend.cpp`.

Access to `IndexManager` from `commit_one_area`: needs the per-`DbArea` index manager handle. **Confirm the accessor** (e.g., `A.indexManager()` / an `orderstate` bridge) — not yet located; see Q2.

---

## 6. Behavioral effects (expected)

- Indexed key `REPLACE` + `COMMIT` on the native lane updates the index in O(log n) per key instead of O(n) rebuild.
- Native index and data become atomic within the LMDB txn boundary; `COMMIT` failure paths abort the index txn and retain the buffer for retry (matches existing semantics).
- `ROLLBACK` unchanged and correct.
- CNX still rebuilds at commit; INX/IDX still reindex.
- Concurrency: bulk txn holds LMDB's single writer for the commit duration (fine for single-user/use-based locking).

---

## 7. Falsifiable exit conditions / proof artifacts

1. **Correctness:** `USE`; `SET ORDER TO <keytag>` (native); `TABLE ON`; `REPLACE key WITH <newval>`; `COMMIT`; `SEEK <newval>` → lands on the record; `SEEK <oldval>` → not found. No `REBUILD`/`BUILDLMDB` between.
2. **Atomic rollback:** buffered multi-record key edits; force a mid-commit failure (locked record) → after partial failure, `SEEK` reflects **no** committed index change for the failed set (bulk aborted), buffer retained.
3. **Read-your-own-writes:** enable `VALIDATE UNIQUE` on the tag; within one `COMMIT`, insert two records with the same new key → second rejected (requires 4.4).
4. **No regression:** CNX table — same REPLACE/COMMIT still rebuilds and `SEEK` correct.
5. **Perf artifact:** 5.5M-row table, single key REPLACE+COMMIT wall-time before/after (expect rebuild-time → sub-ms class), captured to `labtalk/reports/…`.

Status stays `review-needed` until 1–4 are runtime-evidenced.

---

## 8. Open questions

- **Q1.** Does any commit-time path (VALIDATE UNIQUE, TRIGGER, RULE, SET RELATION refresh) issue an index `SEEK` while the bulk txn is open? If yes, 4.4 is mandatory; if no, it can be deferred. *(cmd_validate_unique.cpp / unique_registry.cpp / cmd_trigger.cpp not yet read.)*
- **Q2.** What is the canonical accessor for a `DbArea`'s `IndexManager` from `commit_one_area`? `orderstate::isCdx(A)` exists; need the manager handle it wraps.
- **Q3.** Data/index cross-store atomicity: DBF writes flush during the record loop; the LMDB bulk commits afterward. A crash between DBF flush and `commitBulkWrite` diverges them. Is the `cdxmeta` schema-hash guard + a stale flag an acceptable reconciliation (force rebuild on mismatch), or is a 2-phase marker wanted? Also confirm desired ordering of `commitBulkWrite` vs `journal_note_commit`.
- **Q4.** `CHANGE_INSERT` is noted as not materialized by `apply_one_recno` today — confirm APPEND/commit flow so `apply_insert_snapshot` is hooked at the right site (may belong in `cmd_append`, not COMMIT).
- **Q5.** DUPSORT vs composite: confirm `BUILDLMDB`/`rebuild` create each tag DBI with a single, stable flag policy so mutation-time encoding matches build-time. (Mutation paths already re-derive from live DBI flags — the risk is only inconsistent creation.)
- **Q6.** Multi-tag churn: adopt the 4.5 changed-fields-only optimization now, or keep the simpler all-tags snapshot for v1?
- **Q7.** *(Terminology follow-up)* Standardize "native index" for the CDX/LMDB lane across HELP, manualgen, and the Engine Feature Crosswalk? If adopted, add a glossary entry contrasting native (CDX/LMDB) vs CNX/INX/IDX.

---

## 9. Fallback

If any exit condition fails, revert to current behavior: leave `auto_reindex_if_needed` native-skip as-is and mark the area stale so an explicit `BUILDLMDB`/rebuild restores correctness. The change is additive and gated on `isCdx`; disabling the wrap restores today's semantics.
