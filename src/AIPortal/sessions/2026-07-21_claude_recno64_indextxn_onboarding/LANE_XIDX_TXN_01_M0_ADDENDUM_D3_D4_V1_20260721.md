# M0 Addendum — Lane `XIDX-TXN-01`: D4 closed, D3 recommendation

**Lane:** `XIDX-TXN-01` (LMDB in-transaction index key maintenance)
**Date:** 2026-07-21
**Author:** Claude (hosted AI), source-read only.
**Result:** D4 **RESOLVED** (evidence below). D3 **recommendation issued, ratification-pending** (your design authority). With these, M0 is **met** and the lane is **M1-ready**.

---

## D4 — DBI flag policy (DUPSORT vs composite)  → **RESOLVED**

Evidence: `src/cli/cmd_buildlmdb.cpp`, `build_tag_lmdb_from_field()`.

- Each tag DBI is created with `mdb_dbi_open(txn, tag_name_uc.c_str(), MDB_CREATE, &dbi)` — **no `MDB_DUPSORT`**.
- Storage written: key = fixed-length field value (uppercased + space-padded to `keylen` for `C`) **‖ 8-byte LE recno**; value = 8-byte LE recno. This is **composite mode**.
- `CdxBackend` agrees end-to-end:
  - `open()` sets `composite_mode_ = true`;
  - `make_storage_key(composite=true,…)` = `base‖recno8`, `make_storage_val` = `recno8`;
  - `upsert`/`erase`/`rebuild` re-derive `composite = (flags & MDB_DUPSORT)==0` from the **live DBI flags**, so a non-DUPSORT DBI ⇒ composite ⇒ **matches the build encoding**.

**Conclusion:** build-time and mutation-time encodings are consistent under a single, stable policy (composite/non-DUPSORT). The `MDB_DUPSORT` branch inside `CdxBackend` is **dormant** for this lane.

**Important disambiguation (new):** there are **two** distinct LMDB-based backends — do not conflate:
- `CdxBackend` (this lane, `.cdx` container → LMDB env): **composite, non-DUPSORT**, key `base‖recno8`.
- `LmdbBackend` (standalone `src/xindex/lmdb_backend.cpp`, the separate `SET LMDB` order type): **`MDB_DUPSORT|MDB_DUPFIXED`**, key = bare base, recno as dup value.
They use different envs and different key schemes; they must never share a tag DB. M1 touches only `CdxBackend`.

**Path model confirmed:** public native container `data\indexes\<stem>.cdx` (read via `cdxfile::` for tag discovery) → LMDB key env `data\lmdb\<stem>.cdx.d` (`resolve_lmdb_env_for_cdx`). This reinforces the native-vs-LMDB split: the `.cdx` file holds the tag directory (native format); the LMDB env holds keys. `IndexManager::openCdx` passes the resolved env path into `CdxBackend::open`, so the ".d" suffix logic there is a consistent fallback, not a divergent path.

**Residual (minor, M1 guard):** `BUILDLMDB` builds one tag per **field name** (tag == field). Confirm the commit-time snapshot tag set (`capture_delete_snapshot_for_current_record`, which walks all field-backed tags) aligns with the tags `BUILDLMDB` actually created (it should, since both key off field names). Add an assertion/trace if a snapshot tag has no DBI (`open_dbi_for_tag_` → "tag not found").

---

## D3 — Cross-store (DBF↔LMDB) atomicity  → **recommendation (ratification-pending)**

**Problem restated.** In the M1 design, buffered field writes flush to the DBF during the commit record loop; the LMDB index bulk commits afterward (`commitBulkWrite`). A crash **between** the DBF flush and the LMDB commit leaves data written but index edits lost (bulk aborted on restart) — divergence.

**Options.**
- **(a) Guard + rebuild fallback (recommended for v1).** Keep the existing `cdxmeta` sidecar schema/identity guard and set the area **stale** if the bulk aborts or on detected mismatch at open; a stale LMDB index forces an explicit `BUILDLMDB`/rebuild to reconcile. Cheap, additive, already partially present (cdxmeta exists; stale flag exists). Accepts a bounded post-crash window that is *detectable* and *recoverable*, never silently wrong.
- **(b) Two-phase durability marker.** Write an intent/marker record (in the journal or a sidecar) naming the pending index delta, fsync it before the DBF flush, and replay/rollback the LMDB delta on restart to match the DBF. True crash-atomic data+index; larger build, new recovery path, must interlock with the existing `journal_begin_commit`/`journal_note_commit` write-ahead log.

**Recommendation:** adopt **(a)** for v1 (M1/M2), and record **(b)** as an M3+ hardening option only if a proof scenario shows the post-crash rebuild cost is unacceptable on the default lane. Rationale: (a) is consistent with the engine's current "detect-and-rebuild" stance (`auto_reindex_if_needed`, cdxmeta guard), is additive, and does not entangle M1 with journal-format changes; it degrades to a known-good rebuild rather than to corruption.

**Ordering decision (part of D3):** `commitBulkWrite()` **before** `journal_note_commit()`, and `abortBulkWrite()` on every pre-commit failure exit. This keeps the index atomic with itself and bounded by the same critical section; the residual window is only DBF-flush→LMDB-commit, covered by (a).

**Status:** recommended default = (a). **Awaiting your ratification** before it is treated as the lane's committed durability contract. Not blocking M1 coding, since (a) reuses existing mechanisms; only the M2 crash-window proof depends on the ratified choice.

---

## M0 gate — closeout

| Item | State |
|---|---|
| D1 accessor | ✔ `ensure_manager(A)` / `isCdx()` gate |
| D2 commit-time reads | ✔ none; §4.4 borrow-txn deferred |
| D3 atomicity | ▶ recommended (a); ratification-pending (non-blocking for M1) |
| D4 DBI flag policy | ✔ composite/non-DUPSORT, build↔mutation consistent |
| D5 terminology/profiles | ✔ native=LEGACY own-format; LMDB=default backend |
| Edit sites | ✔ `commit_one_area` / `apply_one_recno`; reuse `index_hooks` seam |

**M0: met.** Lane promotable to **M1-ready**. Next action: draft the M1 patch (bulk wrap + per-record `capture`/`apply_replace` inside the existing lock) as a change-package update to `AI_CHANGE_PACKAGE_LMDB_INDEX_TXN_MAINTENANCE_V1` §4, carrying the (a) durability contract pending your sign-off.
