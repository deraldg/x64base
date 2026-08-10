# M0 Findings — Lane `XIDX-TXN-01` (LMDB in-transaction index key maintenance)

**Lane:** `XIDX-TXN-01`
**Gate:** M0 — Discovery / contracts locked
**Date:** 2026-07-21
**Author:** Claude (hosted AI), source-read only (no edits to `D:\code\ccode`).
**Verdict:** M0 substantially met — D1, D2, D5 resolved; **the M1 design is revised** by a mechanism finding (below). D3, D4 remain open (one decision, one file read).

---

## 0. Headline

Index maintenance for the LMDB lane is **already wired** at the engine write funnel via a neutral hook seam — it is *not* absent. Precisely:

- `DbArea::replaceFieldStored()` (src/xbase/dbarea.cpp) does: lock → `before = index_hooks::capture(*this)` → `set()+writeCurrent()` → unlock → `after = index_hooks::capture(*this)` → `index_hooks::apply_replace(before, after, rn)`.
- `xindex/attach.cpp` installs those hooks: `capture` → `IndexManager::capture_delete_snapshot_for_current_record`, `apply_replace` → `IndexManager::apply_replace_snapshot` → `on_delete/on_append` → `CdxBackend::erase/upsert`.

**Consequence:** `TABLE OFF` REPLACE already maintains the LMDB index per edit (each in its own autocommitted `mdb_txn`). The gap is only the **buffered COMMIT path**, which bypasses the funnel: `apply_one_recno` (src/cli/cmd_commit.cpp) calls raw `A.set()+A.writeCurrent()` — no hooks — and `auto_reindex_if_needed` deliberately **skips** CDX/LMDB. So buffered key commits leave the index unmaintained → this is why rebuild is currently required after buffered key mutation.

---

## 1. D1 — IndexManager accessor  → **RESOLVED**

- Accessor: `xindex::ensure_manager(xbase::DbArea&)` / `xindex::manager_if_attached(area)` (`include/xindex/attach.hpp`, `src/xindex/attach.cpp`). One `IndexManager` per `DbArea`, held in a static map; created on demand; detached on `DbArea::close()`.
- **Preferred commit gate:** `xindex::ensure_manager(A).isCdx()` (live-backend `dynamic_cast<CdxBackend*>`), **not** `orderstate::isCdx(A)` — the latter is only a `.cdx` filename-suffix check on the tracked container path and does not prove a live LMDB backend is open.
- Boundary note: `cmd_commit.cpp` is CLI/composition layer, already guards index work under `DOTTALK_HAS_XINDEX`; it may include `xindex/attach.hpp` and call `beginBulkWrite/commitBulkWrite`. This respects the Optional-Index Architecture Decision (xbase must not name `IndexManager`; the CLI may).

## 2. D2 — Any commit-time index SEEK?  → **RESOLVED: none**

- `cmd_VALIDATE_UNIQUE` is a **manual** command: linear `gotoRec` scan into an in-memory `unordered_map`; it performs **no index seek** and is **not invoked from COMMIT**.
- `unique_registry` is process-local field-name flags (SET UNIQUE); no index reads.
- `commit_one_area` performs no SEEK, and fires no TRIGGER/RULE/VALIDATE.
- `orderhooks::reconcile_after_mutation` opens the **native** `.cdx`/`.cnx` tag directory (`cdxfile::`/`cnxfile::`) to re-validate the active tag — a metadata read, **not** an LMDB key seek — and is not in the commit loop.
- **Therefore the read-your-own-writes borrow-txn fix (change package §4.4) is DEFERRABLE.** It becomes mandatory only if/when uniqueness or triggers are enforced against the LMDB index *during* commit. Reclassify M2 test #4 (VALIDATE UNIQUE) as a **future** uniqueness-enforcement lane, not an M2 exit condition here.

## 3. D5 — Terminology / profiles  → **RESOLVED**

Per `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`, builds select `DOTTALK_INDEX_MODE`:

| Mode | xindex | LMDB backend | Meaning |
|---|:---:|:---:|---|
| `NONE` | absent | absent | physical DBF only; SEEK unknown |
| `LEGACY` | yes | **absent** | CNX/CDX attach via **native** file formats (`cdxfile::`/`cnxfile::`) |
| `LMDB` | yes | **yes** | full provider; keys in LMDB env `<container>.cdx.d`; `.cdx` file holds the tag directory |

This reconciles both of your clarifications:
- **Native indexing** = the CDX/CNX **own file formats** (`cdxfile::`, `cnxfile::`), the key store in `LEGACY` mode — separate from LMDB. ✔ your terminology.
- **LMDB indexing** = the `LMDB`-mode backend (`CdxBackend`+`LmdbBackend`), the **default** in the development profile; `.cdx` here is metadata/tagdir while keys live in the LMDB env. ✔ "LMDB is the default."
- The crosswalk phrase "V64 defaults to `.cdx`" refers to the **container/extension**, which is consistent with both modes; the *backend* behind that `.cdx` differs by profile. (Doc-wording clarification, not a contradiction.)

## 4. Revised M1 design (supersedes change package §4.1 for the buffered path)

Reuse the existing engine seam instead of hand-rolling snapshot calls:

```
commit_one_area(A, area0):
    ... journal_begin_commit ...
    im = xindex::ensure_manager(A)                 # DOTTALK_HAS_XINDEX
    native_lmdb = im.isCdx()                        # live backend, not orderstate string
    if native_lmdb: if !im.beginBulkWrite(&err): abort → FinalizeFailure

    for each recno:
        gotoRec; readCurrent; try_lock_record          # existing use-based lock
        before = native_lmdb ? xbase::index_hooks::capture(A) : {}
        apply agg field set()s + writeCurrent()         # existing raw write (multi-field, once)
        if native_lmdb and ok:
            after = xbase::index_hooks::capture(A)
            xbase::index_hooks::apply_replace(A, before, after, recno)   # routes to bulk_txn_
        unlock_record
    ... memo flush ...
    ... auto_reindex_if_needed (CDX branch now truthfully "maintained") ...
    if native_lmdb: if !im.commitBulkWrite(&err): restore buffer → FinalizeFailure
    ... journal_note_commit ...
```

Why this is better than V1 §4.1:
- **One capture/apply per record** (not per field) — `capture` already walks all field-backed tags, so a whole-record before/after pair covers every changed key; unchanged tags produce equal before/after (delete+reinsert = net no-op).
- **Reuses `xbase::index_hooks::capture/apply_replace`** — the same seam `replaceFieldStored` uses — so CLI does not duplicate key logic and the xbase↔xindex boundary is preserved (CLI only names the neutral seam + the bulk begin/commit).
- **Transactionality for free:** with `bulk_txn_` open, the hook-driven `upsert/erase` route onto the shared txn (confirmed in `cdx_backend.cpp` bulk branches); `commitBulkWrite`/`abortBulkWrite` bind index atomicity to the commit outcome.
- No second record lock (COMMIT already holds it) — avoids the double-lock that routing through `replaceFieldStored` would cause.

`TABLE OFF` path (§4.3) is **already correct today** via `replaceFieldStored` hooks — no change needed for correctness; only optional batching if a single command mutates many rows.

## 5. Exact edit sites (anchors)

- `src/cli/cmd_commit.cpp` → `commit_one_area(...)`: open/commit/abort bulk around the `for (... tb.changes ...)` loop; `apply_one_recno(...)`: insert `capture` before the field-set block and `apply_replace` after `writeCurrent()`. Change `auto_reindex_if_needed` CDX branch message from "skipped" to "maintained".
- `src/xbase/dbarea.cpp` → no change (seam already present; reference implementation for ordering).
- `src/xindex/cdx_backend.cpp` → **only if** D2 flips later (borrow-txn read path); not needed now.

## 6. Remaining M0 items (before M1 exit)

- **D3 (decision, Q3).** Cross-store atomicity: DBF writes flush in the record loop; LMDB bulk commits after. Crash between the two diverges them. Proposed reconciliation: keep the `cdxmeta` schema-hash guard + set the area stale on abort so an explicit `BUILDLMDB`/rebuild recovers. Decide: accept guard-based reconciliation for v1, or add a 2-phase marker. Also confirm ordering: `commitBulkWrite` **before** `journal_note_commit`.
- **D4 (one file, Q5).** Read `src/cli/cmd_buildlmdb.cpp` (+ `cdx_meta`) to confirm each tag DBI is created with a single stable flag policy (DUPSORT dup-value vs composite `base‖recno8` key). Mutation paths already re-derive `composite` from live DBI flags, so the only risk is inconsistent **creation**. `rebuild()` in `cdx_backend.cpp` uses `composite_mode_ = true` + default `mdb_put`; verify `BUILDLMDB` matches.

## 7. Cross-reference

The Optional-Index Architecture Decision's own "remaining proof" list names this lane's territory directly:
- item 1: "attached-CNX replace/append/delete/recall/pack synchronization";
- item 2: "a public-command CDX metadata-to-LMDB workflow".
`XIDX-TXN-01` is the execution of item 2 (LMDB lane) and informs item 1 (native CNX lane, separate follow-up).

## 8. Gate status

M0 exit conditions: D1 ✔, D2 ✔, D5 ✔, edit sites ✔; **D3 (decision) and D4 (one file read) outstanding.** Recommend: read `cmd_buildlmdb.cpp` (closes D4) and take the D3 reconciliation decision, then promote lane to M1-ready and update `AI_CHANGE_PACKAGE_LMDB_INDEX_TXN_MAINTENANCE_V1` §4.1 to the §4 design above.
