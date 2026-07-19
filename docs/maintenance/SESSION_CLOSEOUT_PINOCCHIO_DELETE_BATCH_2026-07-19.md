# Session Closeout — DELETE/RECALL index-write batching (Phase 1.3d)

```yaml
ai_report_audit:
  report_id: AIPR-20260719-001
  project: project.x64base.runtime
  branch: homegrown-cnx-20251112-branch
  baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  access_mode: local_write
  scope:
    - include/xindex/cdx_backend.hpp
    - src/xindex/cdx_backend.cpp
    - include/xindex/index_manager.hpp
    - src/xindex/index_manager.cpp
    - src/cli/cmd_delete.cpp
    - src/cli/cmd_recall.cpp
  authorization_note: >
    Original change only in D:\code\ccode on the existing branch. No branch
    created/switched/renamed; not applied to C:\x64base or GitHub. Correctness-
    critical index/DBF-sync path -- requires a maintainer rebuild + the
    destructive proof (on the disposable SCR_DESTR scratch) before any promotion.
  stage: proven_by_teed_transcript
  proof_log: labtalk/proofs/runs/scale_destructive_teed_20260719T060311Z.log  # sha 0294344D06D66E3F9AECAF28DF10EB0C5A138DF524B5FB490C49BA0080A48925
```

## Problem

`DELETE FOR`/`ALL` and `RECALL ALL` under an active CDX order carried a
~2.5 ms/row surcharge: `CdxBackend::erase`/`upsert` do a full LMDB write
transaction (begin + `mdb_del`/`mdb_put` + **commit/fsync**) **per index key per
row**. A 9,999-row delete ≈ 9,999 commits ≈ 25 s; the v1 500k-row delete ≈ 21 min.
Necessary index maintenance, just un-batched.

## Fix — one transaction per bulk op (chunked)

A **bulk write-transaction mode** on `CdxBackend`:

- `beginBulk`/`commitBulk`/`abortBulk`/`inBulk` manage a single held write txn
  (`bulk_txn_`). While open, `erase()`/`upsert()` append to it and skip their
  per-call commit; the caller commits once.
- `IndexManager::beginBulkWrite`/`commitBulkWrite`/`abortBulkWrite` pass through
  to the CDX backend (no-op/false for non-CDX, which keep per-row behavior).
- `cmd_delete.cpp` `delete_targets_by_recno` and `cmd_recall.cpp` `recall_targets`
  wrap their loops: begin bulk, commit every `kBulkChunk = 10000` rows (bounds the
  txn well under LMDB's dirty-page limit so huge deletes don't overflow), commit
  at the end; abort + "index may need rebuild" warning on any error, then degrade
  to per-row (still correct).

### The load-bearing subtlety — bulk-aware `setTag`

`capture_delete_snapshot_for_current_record()` calls `setTag` per field (via
`with_tag_switched_`), and the normal `CdxBackend::setTag` opens **its own** RO
txn (and a `MDB_CREATE` RW txn for a new tag). Holding `bulk_txn_` open across
that would be a second transaction on the same thread/env → **LMDB deadlock** on
the first delete. Fix: `setTag` now detects `bulk_txn_` and resolves/creates the
tag DBI **inside** that transaction instead of opening its own. `capture` only
otherwise reads DBF fields (`buildActiveTagBaseKeyFromCurrentRecord`), so with
bulk-aware `setTag` the entire bulk op stays in exactly one write transaction.

## Correctness (behavior-preserving)

- Final index state is identical to the per-row path — the same keys are erased/
  inserted, just committed together. DBF marks still happen per-row under lock.
- On any error the batch aborts (index unchanged for that chunk) and warns a
  rebuild is needed; the DBF deletes/recalls still stand (recoverable via
  `REINDEX`). The normal path is now *more* atomic (all-or-nothing per chunk).
- Non-CDX backends and unindexed tables are unaffected (bulk not started).

## Proof

Re-run the disposable destructive battery (mutates only the `SCR_DESTR` clone):

```
cmake --build .\build --config Release
powershell -ExecutionPolicy Bypass -File .\dottalkpp\data\scripts\pinocchio\run_pinocchio_destructive_teed.ps1
```

Expected vs the pre-fix run:
- **D2a `DELETE FOR` under ACTIVE order (~9999 rows): 65.4 s → ~40 s** (the ~25 s
  index-commit surcharge collapses to one commit; the remaining ~40 s is the
  inherent full-table predicate scan, unchanged).
- **D2a ≈ D2b** (order-cleared) now, confirming the surcharge is gone.
- `RECALL ALL` similarly reduced.
- Canaries unchanged: clone COUNT 1000000; `DELETE` 9999 / `RECALL ALL` → 0;
  `PACK` kept 990001; `ZAP` → 0. Any change to these fails the proof.

The dramatic case is large deletes (scan-bounded, not commit-bounded): the v1
500k-row delete would drop from ~21 min of commits to seconds of index writes.

## Proof result (build Jul 19 2026, teed sha 0294344D…)

- **D2a `DELETE FOR` under ACTIVE order (~9999): 65.4 s → 37.8 s.** The ~25 s
  per-row index-commit surcharge is gone; D2a (37.8 s) ≈ D2b order-cleared
  (41.3 s) — both are now just the inherent ~40 s predicate scan.
- No deadlock (the bulk-aware `setTag` fix held) and the run completed clean.
- Canaries green: clone COUNT 1,000,000; `DELETE` 9999; `RECALL ALL` → 0;
  `PACK` kept 990001; reopened COUNT 990001; `ZAP` → 0.
### RECALL directly proven (teed sha 0D15DADF…)

Follow-up proof `pinocchio_recall_batch_proof.dts` keeps the index attached
during `RECALL ALL` (the destructive script had cleared it):

- **RA `RECALL ALL` under ACTIVE order (batched reinsert): 50.7 s** vs
  **RB order-cleared baseline (no reinsert): 49.0 s** — **RA ≈ RB**, batched
  reinsert adds only ~1.6 s for 9999 rows (~0.16 ms/row vs the old ~2.5 ms/row).
- Integrity: `SEEK 50999999` after RA = **0.00024 s, Found** — the recalled key
  was reinserted (a failed reinsert would miss the keyed lookup and fall back to
  a ~57 s walk). `COUNT DELETED` → 0 after each recall; clone COUNT 1,000,000.
- RA completed in scan-time (~50 s), not the O(n²) minutes the per-row-commit
  path would have cost.

Both DELETE and RECALL index-write batching are now directly proven.

## Notes / open

- Cannot compile-test in this environment; the maintainer's build + the
  destructive proof (disposable scratch + correctness canaries) are the gate.
- `kBulkChunk = 10000` is conservative; can be tuned once measured.
