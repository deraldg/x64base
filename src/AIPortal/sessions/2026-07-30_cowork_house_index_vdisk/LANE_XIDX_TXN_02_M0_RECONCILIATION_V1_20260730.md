# M0 Reconciliation -- Lane `XIDX-TXN-02` (CNX/V32 native + CDX-native transactional index mutations)

**Lane:** `XIDX-TXN-02`
**Gate:** M0 re-verification against current source
**Date:** 2026-07-30
**Author:** Claude (hosted AI), **source-read only -- no build, no runtime**
**Evidence tier:** `source-evidenced` (every claim carries a file:line anchor in section 7). No runtime proof. Nothing here is earned above source tier.
**Status:** `review-needed`
**Supersedes nothing.** Amends `LANE_XIDX_TXN_02_M0_FINDINGS_V1_20260721.md` with five items that document did not surface.

---

## 0. Read first

The question posed -- *"the algorithm we used to update LMDB index keys/tags should work with the house index too"* -- is **already a declared lane**. `XIDX-TXN-02` was opened 2026-07-21, M0 was marked **met**, approach **A** (in-memory delta + atomic `save()`) was locked, and the lane was marked **M1-ready**. It has not been implemented.

The sibling lane `XIDX-TXN-01` (LMDB) **did** land: `SET INDEXTXN` exists, and `commit_one_area` gates in-COMMIT bulk maintenance on `Settings::indexTxnOn() && im->isCdx()`. The CNX branch of `auto_reindex_if_needed` still calls `cmd_REBUILD` unconditionally.

So this is not a new idea to evaluate -- it is a ready lane to schedule, plus five blockers below that the 07-21 M0 did not identify.

---

## 1. Direct answer: yes, and more strongly than the premise assumes

The premise says "the algorithm we used for LMDB should work here too." Source says something stronger: **there is no LMDB-specific algorithm.** The delta algorithm is already backend-neutral and already runs for CNX today -- it simply lands on stubs.

Trace:

1. `IIndexBackend` declares `upsert(Key, RecNo)` / `erase(Key, RecNo)` -- pure virtual, no storage assumptions.
2. `xbase::index_hooks` provides the before/after seam: `capture(area)` -> mutate -> `capture(area)` -> `apply_replace(before, after, recno)`. Installed as plain function pointers, so `xbase` knows nothing about key formats or backends.
3. `DbArea` fires it around the physical write, and `cmd_commit.cpp` fires it around buffered apply.
4. `IndexManager::apply_replace_snapshot(before, after, rec)` is the algorithm: **erase every before-key, then insert every after-key, per tag, switching tags around each op.** `on_replace` carries the `old_key == new_key` short-circuit and rollback-on-failure.

There is not one LMDB call in any of that. The four-case delta you're thinking of is present and generic.

**Where it dies:** both house backends implement the two virtuals as discard-and-flag.

```cpp
// batch-family contract: CNX does not incrementally maintain on mutation in v1.
// These just mark the container stale.
void CnxBackend::upsert(const Key& key, RecNo rec) { (void)key; (void)rec; stale_ = true; }
void CnxBackend::erase (const Key& key, RecNo rec) { (void)key; (void)rec; stale_ = true; }
```

`CdxNativeBackend::upsert/erase` are byte-identical in intent. The snapshots are computed, the keys are built, the calls arrive -- and are dropped on the floor. That is the whole of the "must be rebuilt afterward" behavior.

**Consequence for scoping:** this is not an algorithm port. It is *implement two virtual functions and the storage and persistence beneath them.* The orchestration above them is done.

---

## 2. Current state vs. the 2026-07-21 plan

| Item | 07-21 plan | Verified 07-30 |
|---|---|---|
| `SET INDEXTXN` flag, default OFF | proposed | **landed** -- `cmd_set.cpp`, `Settings::indexTxnOn()` |
| LMDB in-COMMIT bulk maintenance (`XIDX-TXN-01` M1) | proposed | **landed** -- `commit_one_area` gate + `beginBulkWrite`/`commitBulkWrite` |
| `CnxBackend::upsert/erase` real | M1 | **not landed** -- still `stale_ = true` |
| `CdxNativeBackend::upsert/erase` real | implied (format-neutral) | **not landed** -- still `stale_ = true` |
| `CnxDocument::save()` | M1 | **not landed** -- returns `false`, `"not implemented"` |
| CNX branch of `auto_reindex_if_needed` (C4) | M1 | **not landed** -- unconditional `cmd_REBUILD` |
| Dirty/stale fail-safe (C3) | "mechanism present" | **mechanism present but unwired** -- see N5 |

---

## 3. Five blockers not in the 07-21 M0 findings

### N1 -- `InxPayload` is immutable by construction

`InxPayload` holds `std::vector<InxEntry> entries_` sorted by key, searched with `std::lower_bound`. It exposes **no** insert or erase. `entries_` is private with a const-only accessor, and the only construction paths are the static builders `fromEntries1Inx` / `fromEntries2Inx`, which take an already-sorted vector.

Approach A says "mutate the loaded in-memory `InxPayload`." There is currently no API through which to do that. This is a small, contained addition -- but it is an addition to a class that was deliberately built read-only, and both `CnxBackend` and `CdxNativeBackend` read through it. Widening it touches both lanes at once.

### N2 -- `pos_by_recno_` is a dense, persisted, position-indexed table

`InxPayload` carries a second structure: `std::vector<std::int32_t> pos_by_recno_`, sized `record_count_snapshot + 1`, mapping recno -> **ordinal position in `entries_`**. It is built at construction and **persisted in the 2INX format** (read back entry-by-entry on load, with its own "truncated 2INX pos-by-recno table" error).

> **Additional gap found during verification:** `InxPayload::writeToStream` is *itself* a stub -- `"InxPayload::writeToStream not implemented"` -- and `writeToFile` merely delegates to it. The persisted 2INX form is written today by CLI code (`cmd_index.cpp`, `cmd_reindex.cpp`), not by the class. So `CnxDocument::save()` has no payload writer to call: **the persistence gap is two layers deep, not one.** M1 must either implement `writeToStream` or factor the existing CLI writer down into the payload class. This is a larger M1b than the 07-21 findings imply.

This is the item with the largest design consequence, and it is absent from the 07-21 analysis:

- Any positional insert or delete in `entries_` **shifts every subsequent element**, invalidating every `pos_by_recno_` value after the insertion point. Maintaining it incrementally is O(n) per mutation -- worse than the vector splice itself.
- It is persisted, so `save()` must emit a consistent table, not a patched one.

**Implication:** per-mutation maintenance of `pos_by_recno_` should not be attempted. Treat it as a derived artifact rebuilt **once** at `save()` (and once at load), and have mutation invalidate rather than update it. That is cheap and correct. It also means any reader depending on `positionOfRecno()` mid-transaction must be identified -- a stale table there returns a confidently wrong position, not an error.

### N3 -- `InxPayload` ordering has no recno tiebreaker (correctness blocker for `erase`)

The comparators are key-only:

```cpp
bool InxPayload::lessEntryKey_(const InxEntry& e, const std::string& key) { return e.key < key; }
```

`seekExact` and `seekFirstGe` both `lower_bound` on key alone. Duplicate keys therefore form an undifferentiated run, and `erase(key, rec)` **cannot identify which entry to remove from the key alone.**

Contrast `IndexTag::PairLess`, which orders on `(key, recno)` correctly -- the pattern already exists in the tree, just not in the structure CNX/CDX-native actually use.

Removing the wrong duplicate is a silent corruption: counts stay right, `SEEK` still hits, and the wrong record is reachable. Resolution options: extend the ordering to `(key, recno)`; or scan the equal-key run for the matching recno; or use `positionOfRecno()` -- which N2 just made unreliable mid-transaction. This must be settled before `erase` is written.

### N4 -- Multi-tag capture is CDX/LMDB-only (prerequisite, not a detail)

`IndexManager::capture_delete_snapshot_for_current_record()` enumerates **all field-backed tags** only when the backend `dynamic_cast`s to `CdxBackend`. Everything else falls to:

> `// CNX / other single-active-tag backend: snapshot only active tag.`

`CnxBackend` and `CdxNativeBackend` are `ITagBackend` but **not** `CdxBackend`, so both take the single-tag path.

**The comment is also wrong about LMDB.** It reads "CDX/LMDB: one tag DB per field-backed tag," but `LmdbBackend` derives from `IIndexBackend` directly, not from `CdxBackend` -- so the standalone LMDB backend fails the same `dynamic_cast` and *also* takes the single-active-tag path. The same narrowing affects `IndexManager::isCdx()`, which is likewise a `CdxBackend`-only cast, and `isCdx()` is what gates `SET INDEXTXN` in `commit_one_area`. Net effect: **in-COMMIT maintenance engages only for `CdxBackend`** -- not for `LmdbBackend`, `CnxBackend`, or `CdxNativeBackend`. Worth confirming that is intended; if the intent was "any tag-capable backend," the predicate should be `dynamic_cast<ITagBackend*>` (or a capability method on the interface) rather than a concrete-class test.

Today this is harmless -- the keys are discarded anyway and rebuild fixes everything. The moment `upsert`/`erase` become real, it stops being harmless: a multi-tag `.cnx` would maintain the active tag correctly and leave every other tag silently skewed, with nothing marking them stale. **This must be fixed in the same change as the upsert/erase implementation, not after it.**

### N5 -- The fail-safe backstop is declared but not wired

C3 in the 07-21 findings says the dirty-flag mechanism is "present." It is present; it is not connected.

- **`wasStale()` has zero callers** anywhere in `src/` or `include/`. Every backend implements it; nothing reads it. So `stale_ = true` in the CNX/CDX-native stubs is a **write-only signal** -- which is precisely why the index "must be rebuilt" by hand rather than automatically.
- **`CNX_HDRF_DIRTY` is never tested.** It is set by `cnxfile::set_dirty` (called only by `cmd_pack` / `cmd_zap`), and cleared unconditionally inside `write_tagdir` and `store_header`. Nothing inspects it at open. The "torn write -> fall back to `rebuild()`" behavior C3 relies on does not exist.
- `TagDirEntry` already reserves `updated_ts` and `stats_rec` -- per-tag freshness fields are available and unused.

**This is the most actionable finding in the document, and it is independently valuable.** Wiring open-time dirty detection and a `wasStale()` consumer is useful *today*, before any incremental maintenance exists: it converts a manual "remember to rebuild" convention into an automatic one, and it is the safety net that makes landing N1-N4 safe rather than risky. LMDB gave the CDX lane atomicity for free; the house lane has to earn it, and this is the cheapest first installment.

---

> **Superseded in part, 2026-07-30 (maintainer correction).** Section 4 item 1 and section 5 below argue for proving the algorithm before building persistence, and propose RAM (`CdxNativeBackend`) as the harness. The argument holds; the harness does not. **x32/CNX is the better prototype target**, because `include/cdx/cdx_document.hpp:20` *includes* `cnx/cnx_document.hpp` and both readers converge on the same `InxPayload` construction -- so N1/N2/N3 are authored once and serve both, and x32 needs no vdisk. Operative version: `TRIAGE_EXECUTION_PLAN_V1_20260730.md`, sitting 6.

## 4. What this changes about the M0 plan

The 07-21 approach decision (A now, B later, C as fallback, authored format-neutrally) still holds -- nothing found contradicts it. The amendments are to sequencing and to two unstated assumptions:

1. **Order of work should invert.** M0 sequenced `save()` and `upsert/erase` first. N5 should go first: it is smaller, it is useful standalone, it is reversible, and it is the guard that makes the rest safe to land behind `SET INDEXTXN`.
2. **N3 is a gate, not a task.** Duplicate-key erase precision must be decided before `erase` is written, or the lane ships silent corruption behind an opt-in flag.
3. **N4 is in scope for M1**, not a follow-up. Single-tag maintenance on a multi-tag container is worse than no maintenance.
4. **N2 changes what "in-memory delta" means.** `pos_by_recno_` should be invalidated-and-rebuilt at `save()`, not maintained. If that proves too coarse, the alternative is a pending-delta overlay merged at save time rather than in-place splicing -- which also bounds the O(n) shift cost that Approach A otherwise pays per mutation.
5. **`CdxNativeBackend` should be named in the lane explicitly.** The 07-21 twin-format finding says a native path authored format-neutrally serves both; but `CdxNativeBackend` is a live backend today (ramfs `.cdx` routing) with the same stubs, so it is not merely a future beneficiary -- it is a second present-tense instance of the same defect.

---

## 5. Suggested revised M1 split

**M1a -- fail-safe plumbing (no behavior change to the fast path).**
Consume `wasStale()`; test `CNX_HDRF_DIRTY` at open and fall back to `rebuild()`; stop `write_tagdir` clearing the flag unconditionally; set it around any write that leaves the container inconsistent. Exit proof: an artificially dirtied `.cnx` reopens into a rebuild, and `SEEK` is correct.

**M1b -- real `upsert`/`erase` + `save()` behind `SET INDEXTXN`.**
N1 (payload mutation API), N3 (recno-precise ordering), N4 (multi-tag capture for all `ITagBackend`s), N2 (`pos_by_recno_` rebuilt at save), `CnxDocument::save()` with temp+fsync+rename, C4 COMMIT branch. Both `.cnx` (V32/uint32) and native `.cdx` (V64/uint64) via the shared primitives.

M2/M3 exit conditions from the 07-21 M0 findings still apply, with the addition of a **multi-tag** regression: mutate a key on a `.cnx` carrying two or more tags, then `SEEK` on the *non-active* tag.

---

## 6. Open questions for you

1. Is `XIDX-TXN-02` actually next, or was it deliberately parked after `XIDX-TXN-01` landed? The lane says M1-ready; nothing records a decision to defer.
2. N3 -- preference on duplicate-key resolution: widen `InxPayload` ordering to `(key, recno)` (cleanest, changes on-disk sort order for equal keys and so touches the format story), or scan the equal-key run (no format impact, O(run length))?
3. Is M1a worth landing on its own regardless of whether M1b is scheduled? My read is yes -- it is a correctness improvement over today independent of incremental maintenance.
4. Does the `.cnx` on-disk sort order need to remain byte-compatible with anything external, or is `CNX_VERSION` free to bump?
5. Is the `CdxBackend`-only narrowing in section N4 (which also excludes `LmdbBackend` from both multi-tag capture and the `SET INDEXTXN` gate) intended, or a concrete-class test that should have been a capability test?
6. Should `InxPayload::writeToStream` be implemented in the class, or should `save()` call down to a factored-out version of the existing `cmd_index.cpp` writer? The former is cleaner; the latter avoids duplicating format knowledge that currently lives in the CLI.

---

## 7. Evidence index

| Claim | Anchor |
|---|---|
| Backend-neutral `upsert`/`erase` | `include/xindex/index_backend.hpp:47-48` |
| Before/after seam | `include/xbase/index_hooks.hpp:26-36`; `src/xbase/index_hooks.cpp:28-40` |
| Seam installed | `src/xindex/attach.cpp:120` |
| Seam fired around physical write | `src/xbase/dbarea.cpp:263, 282-283` |
| Seam fired in COMMIT | `src/cli/cmd_commit.cpp:243-276` |
| The delta algorithm (generic) | `src/xindex/index_manager.cpp:547-576` |
| `old==new` short-circuit + rollback | `include/xindex/index_manager.hpp` (`on_replace`) |
| CNX stubs | `src/xindex/cnx_backend.cpp:519-533` |
| CDX-native stubs | `src/xindex/cdx_native_backend.cpp:507-519` |
| `CnxDocument::save` stub | `src/cnx/cnx_document.cpp:239-244` |
| N1 immutable payload | `include/xindex/inx_payload.hpp:46-51, 71-79` |
| N2 `pos_by_recno_` build + read-back | `src/xindex/inx_payload.cpp:244-251, 314-320` |
| N2 `writeToStream` is a stub; writer lives in CLI | `src/xindex/inx_payload.cpp` (`writeToStream`); `src/cli/cmd_index.cpp:267-289`; `src/cli/cmd_reindex.cpp:390-409` |
| N4 `LmdbBackend` also fails the cast | `include/xindex/lmdb_backend.hpp:38` (derives `IIndexBackend`) |
| N4 `isCdx()` is a concrete-class cast | `src/xindex/index_manager.cpp:85-87` |
| N3 key-only comparators | `src/xindex/inx_payload.cpp:95-127` |
| N3 correct pattern exists | `include/xindex/index_tag.hpp` (`PairLess`) |
| N4 multi-tag capture gate | `src/xindex/index_manager.cpp:489-528` |
| N5 `wasStale()` no consumers | repo-wide grep: declarations only, `include/xindex/*.hpp`, `include/cnx/cnx_backend.hpp` |
| N5 dirty flag set/cleared, never read | `include/cnx/cnx.hpp:26,104`; `src/cnx/cnx_file.cpp:192,271-277`; `src/cli/cmd_pack.cpp:259`; `src/cli/cmd_zap.cpp:222` |
| Unused per-tag freshness fields | `include/cnx/cnx.hpp` (`TagDirEntry.updated_ts`, `.stats_rec`) |
| `SET INDEXTXN` landed | `src/cli/cmd_set.cpp:1446-1470`; `src/cli/cmd_commit.cpp:376-392` |
| CNX still rebuild-on-commit | `src/cli/cmd_commit.cpp:319-330` |
| Backend routing | `src/xindex/index_manager.cpp:114-125, 221, 258` |
| V32/V64 ceilings | `include/cnx/cnx_backend.hpp:44`; `include/xindex/cdx_native_backend.hpp:54` |

---

## 8. Delivery note

Per the Outside-AI Delivery Rule this is a `review-needed` draft for review and placement, not an edit to `D:\code\ccode`. No source was modified. Suggested home: `src/AIPortal/sessions/2026-07-30_.../`, filed against lane `XIDX-TXN-02`.
