# M1 Apply Manifest — Lane `XIDX-TXN-01` (LMDB in-COMMIT index maintenance)

**Date:** 2026-07-21 · **Status:** `review-needed` source drop, compilable against the current tree.
**Baseline confirmed:** your `datarun` proved the gap — buffered `REPLACE`+`COMMIT` then `SEEK ZZ_TXN_BUFFERED` → **Not found** (stale index), with `SET INDEXTXN` unrecognized (flag not yet compiled in). This manifest adds the flag + the transactional path.

---

## 1. Files in this drop

| Deliverable file | Target in repo | Kind |
|---|---|---|
| `settings.hpp` | `include/cli/settings.hpp` | full replacement (adds `index_txn_on` + `indexTxnOn()/setIndexTxn()` + `DOTTALK_INDEX_TXN` env default) |
| `cmd_set.SET_INDEXTXN.patch` | `src/cli/cmd_set.cpp` | unified diff (adds the `SET INDEXTXN ON|OFF` branch after `SET DELETED`) |
| `cmd_commit.cpp` | `src/cli/cmd_commit.cpp` | full replacement (flag-gated bulk wrap + per-record `index_hooks` capture/apply + `orderhooks::reconcile_after_mutation` at commit) |

No other files change. `xbase.lib`, `xindex.lib`, `memo.lib` are unmodified — the change is CLI-layer only, reusing existing `IndexManager`/`index_hooks`/`CdxBackend`/`orderhooks` symbols already linked into the CLI. `cmd_commit.cpp` now also `#include "cli/order_hooks.hpp"` and, after a maintained commit, calls `orderhooks::reconcile_after_mutation(A)` so ordered browsers/relations (ERSATZ, SMARTBROWSE, REL ENUM/JOIN — all of which materialize an ordered recno vector from the index) rebuild from the maintained backend rather than a stale nav-cache snapshot.

## 2. Apply

```
# from D:\code\ccode  (a fresh source drop is a good idea: ./backup_source_drop.ps1)
copy  <drop>\settings.hpp    include\cli\settings.hpp
copy  <drop>\cmd_commit.cpp  src\cli\cmd_commit.cpp
git apply <drop>\cmd_set.SET_INDEXTXN.patch      # or paste the branch manually (see patch)
```

If `git apply` refuses (whitespace/CRLF), the patch is small and self-contained — paste the `if (opt == "INDEXTXN") { ... }` block immediately after the `SET DELETED` block in `cmd_set.cpp`.

## 3. Build

```
cmake --build build --config Release --target dottalkpp
```

Expected: `cmd_set.cpp` and `cmd_commit.cpp` recompile; `dottalkpp.exe` links. No new libs.

## 4. Test (same script, now with the flag live)

Run `index_txn_lmdb_maintenance.dts` (already registered as `INDEX_TXN`, or via your `datarun`). The script now issues `SET INDEXTXN ON` after index setup.

**Expected POST-apply output (the flip):**

| Line | Pre-apply (what you saw) | Post-apply (expected) |
|---|---|---|
| `SET INDEXTXN ON` | SET usage dump (unrecognized) | `SET INDEXTXN: ON` |
| STEP 2 `COMMIT` | `CDX/LMDB rebuild skipped …` | still prints skip (the *rebuild* is skipped) **but** the bulk maintenance ran inside COMMIT |
| STEP 2 `SEEK ZZ_TXN_BUFFERED` | **Not found** | **Found at 12**, `TUP` LNAME = ZZ_TXN_BUFFERED |
| STEP 2b ordered `BOTTOM` (LNAME) | a real last name | **ZZ_TXN_BUFFERED** (sentinel sorts last, now in materialized order) |
| STEP 4 `SEEK ZZ_TXN_BUFFERED` (after delete) | Not found (never indexed) | **Not found** (indexed by STEP 2, then erased on delete) |

The decisive lines are **STEP 2 `SEEK` flipping Not found → Found at 12** (raw index) and **STEP 2b ordered `BOTTOM` landing on the sentinel** (materialized-order / browser+relation path). Together they are the M2 `runtime-evidenced` proof.

Sanity toggles:
- `SET INDEXTXN OFF` then rerun STEP 2 → `SEEK ZZ_TXN_BUFFERED` back to **Not found** (legacy path; proves the flag gates cleanly and the default is safe).
- `env DOTTALK_INDEX_TXN=1` seeds ON without the SET line (for headless CI).

## 5. What the code does (post-apply, flag ON, CDX order)

`commit_one_area`: after `journal_begin_commit`, if `Settings::indexTxnOn() && ensure_manager(A).isCdx()` → `beginBulkWrite()` (one LMDB rw txn). `apply_one_recno` captures the pre-image (`index_hooks::capture`) before the field write and calls `index_hooks::apply_replace(before, after, rn)` after — empty `after` on DELETE (erase). `commitBulkWrite()` runs before `journal_note_commit`; every failure path `abortBulkWrite()` + `set_stale` so `BUILDLMDB` reconciles (D3 option a). `auto_reindex_if_needed` still prints the CDX "skipped" line (cosmetic — the rebuild is indeed skipped; maintenance happened in the bulk). If you want that message to read "maintained", that's a one-line message-catalog change, noted separately.

## 6. Rollback

Restore the three files from your source drop and rebuild. Or leave them in place and simply never turn the flag on — `SET INDEXTXN OFF` (default) is byte-for-byte the old behavior.

## 7. Open items (unchanged)

- D3(a) ratification (durability contract) and the partial-commit policy (this drop **commits** the bulk on partial record failure — §5 of the M1 patch doc).
- `CHANGE_INSERT`/APPEND maintenance is out of scope (COMMIT doesn't materialize inserts) — separate follow-up.
- Optional: `CommitCdxMaintainedText` message so the COMMIT line reads "maintained" when the flag is ON.
