# Findings -- Index Mutation Seam Trace (REPLACE / CALCWRITE / REPLACE_MULTI on CDX-LMDB x64)

**Date:** 2026-07-30
**Run:** `DECLARED-CAPABILITY-VALIDATOR-20260730` - **Author:** Claude (Cowork, local read) - **Owner:** `member.derald`
**Baseline:** `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`
**Evidence tier:** `source-evidenced`. Source-read only. No build, no runtime, no `.dts`.
**Status:** `review-needed`
**Question traced:** how does `REPLACE` handle updating an indexed field in a CDX/LMDB x64 table, given that `REPLACE` and `CALC`/`CALCWRITE` share a mutator factory?

---

## 0. Answer first

**The immediate path works.** `REPLACE` on an indexed field in a CDX/LMDB x64 table does maintain the index, via `DbArea::replaceFieldStored` and the `xbase::index_hooks` seam. `CALCWRITE` reaches the same seam. Nothing is broken in the primary case.

The trace surfaced four secondary findings and one minor one. Two are performance/DRY defects in the seam itself, one is a set of mutators that bypass the seam entirely, and one is a designed asymmetry worth stating plainly because it is the opposite of what a reader would guess.

## 1. The traced path

`cmd_REPLACE` (`src/cli/cmd_replace.cpp:806`):

1. Parse `<field> WITH <value>`; resolve `field1`; require `recno64() != 0`.
2. Evaluate the RHS through `dottalk::expr::eval_rhs`, canonicalizing to a locale-independent string (`:851-908`; the `std::to_chars` fixed-notation path exists because default ostream precision was silently truncating B/Y values).
3. Currency pair normalize -> x64 memo stored value -> `validate_field_value_for_store`.
4. **Fork on buffering** (`:938`):
   - `table::is_enabled(area0)` true -> `tb.add_change(...)`, optional `.tbj` journal note under `RamJournal`, `set_dirty`, `mark_stale_field`, **return**. The index is not touched here.
   - false -> immediate path, below.
5. Immediate: capture `before = A.get(field1)`, then `A.replaceFieldStored(field1, stored_value, &write_err)` (`:990`). **This call is the seam.**

`DbArea::replaceFieldStored` (`src/xbase/dbarea.cpp:232-292`):

6. Validate `field1`, require a current record.
7. `xbase::locks::try_lock_record(*this, rn)`.
8. `before_snap = index_hooks::capture(*this)` (`:263-266`).
9. `ok = set(field1, stored_value) && writeCurrent()` (`:268`).
10. `xbase::locks::unlock_record(*this, rn)`.
11. `after_snap = index_hooks::capture(*this)`; `index_hooks::apply_replace(*this, before_snap, after_snap, rn)` (`:282-283`).

Hook resolution (`src/xindex/attach.cpp`):

12. `capture_hook` -> `manager_if_attached(area)`. Null when no index is attached, yielding an empty snapshot, so an unindexed area costs nothing.
13. -> `IndexManager::capture_delete_snapshot_for_current_record()` (`src/xindex/index_manager.cpp:489`). For a `CdxBackend` the `dynamic_cast` succeeds and the method **enumerates every field-backed tag**, calling `with_tag_switched_` then `buildActiveTagBaseKeyFromCurrentRecord()` for each, collecting `(tag_upper, key)` pairs.
14. `apply_replace_hook` -> `IndexManager::apply_replace_snapshot(before, after, rec)` (`:547-576`): loop `before` calling `on_delete`, then loop `after` calling `on_append`.
15. -> `CdxBackend::erase` / `upsert` (`src/xindex/cdx_backend.cpp:411+`, `:463+`) -> `mdb_del` / `mdb_put`.

`CALCWRITE` reaches the identical seam at `src/cli/cmd_calcwrite.cpp:925`. Its comment at `:918` explicitly warns against `set()` + `writeCurrent()` "because that bypasses the ... index". That comment is correct, and section 4 lists three commands that do it anyway.

## 2. Finding A -- the no-op short-circuit is dead on this path

`IndexManager::on_replace` (`include/xindex/index_manager.hpp`) carries the correct guard:

```cpp
void on_replace(const Key& old_key, const Key& new_key, RecNo rec) {
    if (!backend_) return;
    if (old_key == new_key) return;      // <-- the short-circuit
    ...
}
```

`apply_replace_snapshot` **never calls it.** It calls `on_delete` for every before-key and `on_append` for every after-key, with no per-tag comparison (`index_manager.cpp:547-576`).

Consequence for a single-field `REPLACE` on a table with N field-backed tags:

| Step | Cost |
|---|---|
| `capture` before | N tag switches, N key builds |
| `capture` after | N tag switches, N key builds |
| `apply_replace_snapshot` | N `mdb_del` + N `mdb_put` |
| LMDB transactions | **2N** (one per call outside bulk mode) |

Only one tag's key actually changed. The other N-1 are deleted and reinserted identically.

Outside bulk mode each `upsert`/`erase` opens its own write transaction, re-opens the tag DBI inside it, commits, and calls `reset_ro_txn_()` (`cdx_backend.cpp:431-460`). So the cost is 2N committed transactions plus 2N read-transaction resets, not merely 2N map operations.

**Fix shape:** diff the two snapshots by `(tag, key)` before applying, and emit only the differences. This is a small, self-contained change in `apply_replace_snapshot` and does not touch any backend. It is the same class of per-row waste AIF-046 chased in the expression evaluator, at considerably lower cost to fix.

## 3. Finding B -- three parallel implementations of one seam

| Implementation | Site | Used by |
|---|---|---|
| Hook-based | `src/xbase/dbarea.cpp:263-283` | `REPLACE`, `CALCWRITE` |
| Hand-rolled | `src/cli/cmd_replace_multi.cpp:711-718, 878-907` | `REPLACE_MULTI` |
| Hand-rolled | `src/cli/cmd_commit.cpp:243-276` | buffered `COMMIT` |

`cmd_replace_multi.cpp:869-871` says so in its own words: *"This mirrors `DbArea::replaceFieldStored()`, but keeps REPLACE_MULTI's single lock and single physical write."* The divergence is deliberate and the reason is legitimate (one lock, one write for a multi-field edit). The result is still three copies of capture-write-capture-apply that can drift independently, and they already differ in error handling (Finding E).

Per AIF-037 "Representative by Design" and the Rule of Three, the third copy is the consolidation signal. A shared helper taking the write action as a callable would serve all three without costing `REPLACE_MULTI` its single-write property.

## 4. Finding C -- three mutators bypass the seam entirely

| Site | Pattern | Index maintained? | Stale marked? |
|---|---|---|---|
| `src/cli/cmd_sql_update.cpp:296-298` | `A.set()` + `A.writeCurrent()` | **no** | **no** |
| `src/cli/cmd_sql_insert.cpp:197-199, 227-228` | `A.set()` + `A.writeCurrent()` | **no** | **no** |
| `src/cli/cmd_validate_unique.cpp:352-353` | `A.set()` + `A.writeCurrent()` (repair path) | **no** | **no** |

`DbArea::writeCurrent` (`src/xbase/record_view.cpp:186`) carries no hook. The hook lives only in `replaceFieldStored`. So these three write the record and leave the index pointing at the old key, with **nothing recording that it happened** -- not even `mark_stale_field`, which the buffered and `REPLACE_MULTI` paths both set.

Severity is uneven:

- `cmd_sql_update` / `cmd_sql_insert` carry `status: experimental` in their `@dottalk.usage` blocks, and AIF-074 already established that the early SQL group is abandoned pre-maturity work published as supported. This is further evidence for that lane rather than a new fire.
- `cmd_validate_unique` carries `status: supported` and its bypass is in the `doRepair` path, which mutates a field chosen precisely because it is a uniqueness candidate -- that is, a field that is very likely indexed. This one deserves its own look.

For contrast, `APPEND` does it correctly: `src/cli/append_support.cpp:258-282` calls `ensure_manager`, `capture_delete_snapshot_for_current_record`, and `apply_insert_snapshot`.

## 5. Finding D -- immediate mode maintains the index; buffered mode does not

This is the reverse of the intuitive expectation and is worth stating explicitly.

| Mode | Index maintained at write? | Reconciliation |
|---|---|---|
| `TABLE BUFFER OFF` (immediate) | **yes**, per write, via the hook | none needed |
| `TABLE BUFFER ON` + `SET INDEXTXN OFF` (**default**) | **no** | manual `BUILDLMDB` |
| `TABLE BUFFER ON` + `SET INDEXTXN ON` | yes, batched at COMMIT | none needed |

With the default flag state, `auto_reindex_if_needed` returns early for CDX (`cmd_commit.cpp:310-318`, `CommitCdxSkippedText`) and the COMMIT bulk wrap is gated on `Settings::indexTxnOn() && im->isCdx()` (`:378-384`). This is by design and documented, but a user who turns buffering on for performance silently loses the index maintenance they had without it.

## 6. Finding E (minor) -- index maintenance failure is invisible on the immediate path

`dbarea.cpp:283` discards the result:

```cpp
(void)index_hooks::apply_replace(*this, before_snap, after_snap, rn);
```

A thrown exception sets `*err` only when `err` is already empty; a plain `false` return is dropped entirely. `replaceFieldStored` then returns `true` in both cases, and `cmd_REPLACE` only tests `ok`. So a failed index update on the immediate path produces no message and no stale mark.

`cmd_replace_multi.cpp:900-914` handles the same failure better: on `!idx_ok` it calls `mark_stale_field` for every changed field. The hook path should do at least that much.

## 7. Incidental -- the no-LMDB build

`src/xindex/cdx_backend.cpp:20-50` compiles a `#if !XINDEX_HAVE_LMDB` stub set in which `upsert` and `erase` are empty (not even `stale_ = true`). This is unreachable in practice because the same stub set makes `open()` return `false`, so the backend never attaches. Noted only so a future reader does not mistake it for a fourth silent-drop path. It is a genuine no-op rather than a defect.

## 8. Routing

| Finding | Owning lane | Note |
|---|---|---|
| A -- dead short-circuit, 2N transactions | `XIDX-TXN-01` (LMDB lane, M1 landed) | A defect in landed work, not in a planned lane. Small self-contained fix in `apply_replace_snapshot`. |
| B -- three copies of the seam | AIF-037 Rule of Three; touches `XIDX-TXN-01`/`-02` | Consolidation, not behavior. |
| C -- three bypassing mutators | AIF-074 for the SQL pair; **unassigned** for `cmd_validate_unique` | The `supported`-status one is the live question. |
| D -- buffered/immediate asymmetry | documentation only | Consider stating it in `SET INDEXTXN` HELP and the table-buffer docs. |
| E -- silent maintenance failure | `XIDX-TXN-01` | One line plus a stale mark. |

None of these require a new AIF number. Finding A is the one with a measurable payoff and the smallest diff.

## 9. Evidence index

| Claim | Anchor |
|---|---|
| `REPLACE` fork on buffering | `src/cli/cmd_replace.cpp:938` |
| `REPLACE` immediate seam call | `src/cli/cmd_replace.cpp:990` |
| `CALCWRITE` same seam, with the warning comment | `src/cli/cmd_calcwrite.cpp:918, 925` |
| Hook fired around the write | `src/xbase/dbarea.cpp:263-266, 268, 282-283` |
| Hook installation and manager lookup | `src/xindex/attach.cpp:36-66, 74-88, 113-120` |
| Multi-tag capture, CDX branch | `src/xindex/index_manager.cpp:489-528` |
| `apply_replace_snapshot` (no per-tag diff) | `src/xindex/index_manager.cpp:547-576` |
| `on_replace` short-circuit (uncalled here) | `include/xindex/index_manager.hpp` |
| `CdxBackend::upsert` txn-per-call, non-bulk | `src/xindex/cdx_backend.cpp:411-461` |
| `CdxBackend::erase` | `src/xindex/cdx_backend.cpp:463+` |
| `REPLACE_MULTI` hand-rolled seam + its comment | `src/cli/cmd_replace_multi.cpp:706-718, 866-914` |
| COMMIT hand-rolled seam | `src/cli/cmd_commit.cpp:243-276` |
| `writeCurrent` has no hook | `src/xbase/record_view.cpp:186` |
| SQL UPDATE bypass | `src/cli/cmd_sql_update.cpp:296-298` |
| SQL INSERT bypass | `src/cli/cmd_sql_insert.cpp:197-199, 227-228` |
| VALIDATE UNIQUE repair bypass, `status: supported` | `src/cli/cmd_validate_unique.cpp:352-353`; usage block line 26 |
| APPEND does it correctly | `src/cli/append_support.cpp:258-282` |
| CDX skipped at COMMIT by default | `src/cli/cmd_commit.cpp:310-318, 378-384` |
| No-LMDB stub set | `src/xindex/cdx_backend.cpp:20-50` |

## 10. Delivery note

`review-needed` draft. No source modified. Filed into the existing 2026-07-30 session package rather than opening a lane, per the maintainer's split-by-nature ruling: these are defects and observations routed to lanes that already exist.
