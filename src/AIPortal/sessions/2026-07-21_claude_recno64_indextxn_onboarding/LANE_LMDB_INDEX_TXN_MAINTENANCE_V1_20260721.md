# LANE — LMDB-Lane In-Transaction Index Key Maintenance

**Lane code:** `XIDX-TXN-01`
**Lane name:** LMDB in-transaction index key maintenance (replace rebuild-on-mutation)
**Status:** `planned lane`  *(not yet earned: no source landed, no runtime evidence)*
**Owner:** Derald (engine) · drafting partner: Claude (hosted AI, change-package delivery only)
**Created:** 2026-07-21
**Change package:** `AI_CHANGE_PACKAGE_LMDB_INDEX_TXN_MAINTENANCE_V1_20260721.md`

> **Authority hierarchy (governing rule).**
> Conventions suggest. Registration declares. Metadata records. Runtime proves. Validators enforce.
> This file *declares* the lane. It does not promote status — status is earned per gate below by proof artifacts, not by assertion.

---

## 1. One-line

Maintain LMDB-lane (default `CdxBackend`/`LmdbBackend`) index keys incrementally inside the existing COMMIT record-lock + write-ahead-journal critical section, so an indexed key mutation stops forcing a full rebuild.

## 2. Why a lane

LMDB is the default index lane, so this is the primary mutation path. The incremental machinery already exists (`beginBulkWrite`/snapshots/`commitBulkWrite`, `upsert`/`erase`) but is not wired into `commit_one_area`; today `auto_reindex_if_needed` skips the LMDB lane, leaving the index stale until an out-of-band `BUILDLMDB`/rebuild. This lane closes that gap and makes index+data commit/roll back together.

## 3. Scope

**In:** `cmd_commit.cpp` (bulk wrap + per-recno snapshot apply), `cmd_replace.cpp` `TABLE OFF` autocommit path, `cdx_backend.cpp` read-your-own-writes borrow-txn fix, message/contract updates.
**Out (unchanged):** CNX rebuild path, INX/IDX reindex path, **native `.cdx` own-format lane**, `lmdb_backend.cpp` standalone path, ROLLBACK (stays index-neutral by design).

## 4. Dependencies / preconditions

Blocking discovery items carried from the change package (must be answered before M1 exit):

- **D1 (=Q2)** — accessor for a `DbArea`'s `IndexManager` from `commit_one_area`.
- **D2 (=Q1)** — whether any commit-time path (VALIDATE UNIQUE / TRIGGER / RULE / SET RELATION) seeks the index while the bulk txn is open → decides if the borrow-txn fix is mandatory at M1 or deferrable.
- **D3 (=Q4)** — APPEND/`CHANGE_INSERT` materialization site (`apply_insert_snapshot` may belong in `cmd_append`, not COMMIT).
- **D4 (=Q5)** — `BUILDLMDB`/`rebuild` create each tag DBI with a single stable DUPSORT-vs-composite flag policy.
- **D5 (=Q7)** — terminology reconciliation: native (own `.cdx`) vs LMDB (default) vs CNX in crosswalk/HELP/manualgen; confirm crosswalk "V64 defaults to `.cdx`" wording vs "LMDB is default".

## 5. Milestone gates (falsifiable exit conditions + proof artifacts)

Promotion is left-to-right; a gate is earned only when its exit conditions are proven by the named artifact.

### M0 — Discovery / contracts locked  → promotes lane to `source-evidenced` readiness
**Exit:** D1–D5 answered in writing; the exact edit sites in `commit_one_area` and the `CdxBackend` read paths identified with line anchors.
**Proof:** an M0 findings note appended to the change package (contracts read + answers to D1–D5).

### M1 — Implementation landed  → status `source-evidenced`
**Exit:** patch compiles on Windows/MSVC and WSL/Ubuntu; bulk wrap present in `commit_one_area`; `TABLE OFF` autocommit present; borrow-txn read path present if D2 = yes. No behavior claimed yet.
**Proof:** build logs (both toolchains) + reviewed diff manifest; `git` sha recorded.

### M2 — Correctness + atomicity proven  → status `runtime-evidenced` (candidate `active beta`)
**Exit (all must pass, no rebuild between steps):**
1. `REPLACE key WITH new` → `COMMIT` → `SEEK new` hits, `SEEK old` misses.
2. Forced mid-commit failure (locked record) → failed set shows **no** committed index change (bulk aborted), buffer retained for retry.
3. `ROLLBACK` after buffered key edits → index unchanged, `SEEK old` still hits.
4. `VALIDATE UNIQUE`: two records, same new key, one `COMMIT` → second rejected (exercises read-your-own-writes).
5. CNX regression table → still rebuilds and seeks correctly.
**Proof:** a DotScript regression script in `tests/` + captured transcript; add to `cmd_regression` suite.

### M3 — Default-lane hardening + perf  → status `active beta` → promotion toward default-on
**Exit:** 5.5M-row table, single indexed key `REPLACE`+`COMMIT` wall-time drops from rebuild-class to sub-ms/near-O(log n); crash-window reconciliation (D3/Q3) decided and documented (cdxmeta stale-guard vs 2-phase marker); multi-tag churn optimization (4.5) decision recorded.
**Proof:** perf report at `labtalk/reports/selfdoc/xidx_txn_bench_v1.md` (before/after); reconciliation decision note.

## 6. Status ledger

| Date | Gate | Status | Evidence |
|---|---|---|---|
| 2026-07-21 | — | `planned lane` | This lane declaration + change-package draft (source-read only) |
| 2026-07-21 | M0 | partially met (D1/D2/D5 ✔, D3/D4 open) | `LANE_XIDX_TXN_01_M0_FINDINGS_V1_20260721.md` |
| 2026-07-21 | M0 | **met** — D4 ✔ (composite/non-DUPSORT, build↔mutation consistent); D3 recommendation (a) ratification-pending (non-blocking) | `LANE_XIDX_TXN_01_M0_ADDENDUM_D3_D4_V1_20260721.md` |
| | M1 | **ready** (design revised — reuse `index_hooks` seam + bulk wrap; durability contract (a) pending sign-off) | |
| 2026-07-21 | M1 | **patch drafted** (`review-needed`, not compiled) — awaiting D3(a) + partial-commit-policy sign-off, then build both toolchains | `AI_CHANGE_PACKAGE_LMDB_INDEX_TXN_MAINTENANCE_M1_PATCH_V1_20260721.md` |
| 2026-07-21 | M1 | **flag-gated** — new path behind `SET INDEXTXN` (default **OFF** = legacy batch rebuild retained); lands dark, opt-in for testing | `XIDX_INDEX_MAINTENANCE_FLAG_V1_20260721.md` |

> **Maintenance-mode flag:** the transactional path is gated by `SET INDEXTXN` (default OFF). OFF reproduces today's behavior exactly (LMDB skip + manual `BUILDLMDB`); the batch-rebuild capability is permanent. See the flag decision doc.
| | M2 | pending | |
| | M3 | pending | |

> **M0 mechanism finding (revises M1):** LMDB index maintenance is already wired via the `xbase::index_hooks` seam in `DbArea::replaceFieldStored`, so `TABLE OFF` REPLACE already maintains the index. The gap is the **buffered COMMIT path** (`apply_one_recno` uses raw `set`+`writeCurrent`, bypassing the seam; `auto_reindex_if_needed` skips CDX). M1 = wrap COMMIT's apply loop in `beginBulkWrite`/`commitBulkWrite` and fire `index_hooks::capture`/`apply_replace` once per record inside the existing lock. See M0 findings §4.

## 7. Risks / watch items

- **Cross-store atomicity:** DBF flush and LMDB commit are two durable stores; crash window between them (Q3). Mitigation candidate: `cdxmeta` schema-hash guard forces rebuild on mismatch.
- **Read-your-own-writes:** UNIQUE/trigger seeks during the open bulk txn need the borrow-txn fix or they see a stale snapshot.
- **Single-writer hold:** bulk txn holds LMDB's writer for the commit duration — fine under use-based locking / single user; revisit if concurrency model changes.
- **Encoding drift:** DUPSORT vs composite must match between build and mutation (D4).

## 8. Fallback / de-risk

Additive and gated on `isCdx`. If any M2 condition fails, disable the wrap (revert to `auto_reindex_if_needed` LMDB-skip + stale flag → explicit `BUILDLMDB`) with no data-format change. Lane returns to `planned lane`.

## 9. Register

- Lane code `XIDX-TXN-01` — reserve in the lane registry.
- Related lanes: native `.cdx` own-format maintenance (not yet a lane; would need its own mutable-tree write path — candidate follow-up `XIDX-NATIVE-0x`), CNX incremental B-tree (header reserves `root_page_off`; candidate follow-up).
