# DotTalk++ ACID Assessment — beta-1

Status: Re-rating of the buffered x64 lane after the table-buffer WAL.
Verified: 2026-07-19
Supersedes: `acid_assessment_beta-0.md` (retained as historical).
Overall rating: **Partial** (scoped to buffered-lane Atomicity + Durability; all
other lanes and properties remain **Unverified**).

## What changed since beta-0

beta-0 (2026-07-11) rated every property **Unverified** and recorded, as a
source-defined limit, that "persistent commit-journal and rollback-journal hooks
are currently stubs." On 2026-07-19 the table-buffer transaction path gained a
durable **write-ahead redo log** (WAL), which converts that stub into a
proof-backed mechanism for the buffered x64 lane. This document re-rates only
that lane's Atomicity and Durability; nothing else moves.

## Re-rating evidence (rating gate)

The rating gate requires each moved rating to identify the mechanism, setup,
expected observation, actual observation, and a durable proof artifact.

- **Mechanism.** A text `.tbj` redo log sidecar next to the DBF. Buffered writes
  append `U`/`D` redo records; `COMMIT` writes an atomic `C <count>` marker and
  `fsync`s it (`FlushFileBuffers`/`fsync`) **before** applying to the DBF;
  `ROLLBACK` discards the log; recovery-on-open replays a `C`-marked log
  (idempotent redo) and discards an unmarked one. Standard redo-WAL: commit is
  atomic with respect to a crash.
- **Setup.** `TABLE BUFFER ... PERSISTENT` (RamJournal mode) on a disposable
  table; buffered `REPLACE`/`CALCWRITE`/`DELETE`; a simulated crash between the
  fsync'd marker and the DBF apply.
- **Expected.** A committed buffered transaction survives a crash (its redo is
  replayed on reopen); an uncommitted one leaves the DBF untouched; multiple
  retained edits per field are preserved.
- **Actual.**
  - Phase A — `COMMIT` applied `Alpha2`, `ROLLBACK` kept `Beta`, and history mode
    retained 3 edits (seq 1/2/3) with `COMMIT` landing the highest priority.
  - Phase B — a simulated crash left an uncommitted log; appending the `C` marker
    and reopening replayed it (`NAME=Recovered`); the log was removed.
  - Phase C — buffered `DELETE` deferred to `COMMIT` and was discarded on
    `ROLLBACK`.
- **Durable proof artifacts (hash-verified teed transcripts).**
  - `labtalk/proofs/runs/wal_phaseA_proof_teed_20260719T080435Z.log` — sha256
    `938D4EC361EB34D8D7A3130E62ABDC06F8868DF3C75698C002F6FBE1A6292F60`
  - `labtalk/proofs/runs/wal_phaseB_verify_teed_20260719T081647Z.log` — sha256
    `16B938E4A8DA362EFE54B15E022922210CAD9117232DCF6D227CDAC21D500C7A`
  - `labtalk/proofs/runs/wal_phaseC_proof_teed_20260719T082345Z.log` — sha256
    `FBA1FC92FA1CC531B8B54094D8BC644B1FA51DD13B35053D02775511A257EE54`
  - Design + closeout: `docs/maintenance/TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`,
    `docs/maintenance/SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md`.

## Property ratings

| Property | Rating | Current evidence | Missing evidence |
| --- | --- | --- | --- |
| Atomicity | **Partial** (buffered lane) | Buffered `COMMIT` is all-or-nothing w.r.t. a crash via the fsync'd `C` marker + idempotent recovery replay (proofs above). | Multi-store atomicity across DBF + memo + index in one transaction; non-buffered/direct paths. |
| Consistency | Unverified | Dirty/stale state is visible; `COMMIT` still excludes CDX/LMDB rebuild. | Invariants after direct mutation, commit, and injected multi-store failures. |
| Isolation | Unverified | Buffered state and per-record commit locking exist in source. | Concurrent reader/writer and multi-writer visibility, conflict, and lock tests. |
| Durability | **Partial** (buffered lane) | Committed buffered transactions are crash-recoverable via the fsync'd `.tbj` redo log (proofs above). | Portable DBF `fsync` after replay; CDX/LMDB reconciliation after a buffered commit; the same for non-buffered paths, memo, and power-loss. |

## Lane matrix

| Lane | Rating | Reason |
| --- | --- | --- |
| Buffered x64 mutation | **Partial** | Atomicity + Durability proven via the WAL (above); Consistency (index reconciliation) and Isolation still open. |
| Direct `MULTIREP` | Unverified | Autocommit/non-transactional behavior still unverified. |
| LMDB tag mutation | Unverified | LMDB-local transaction boundaries need source + runtime evidence. |
| DBF + LMDB combined | Unverified | `COMMIT` does no incremental CDX/LMDB maintenance; a buffered commit needs a `REINDEX`. |
| Memo + DBF combined | Unverified | Payload/reference crash recovery unverified. |
| Legacy indexes | Unverified | No guarantee inherited from the x64 lane. |

## Remaining open items for the buffered lane

- Portable DBF `fsync` after replay/commit (`std::fstream` doesn't expose the OS
  handle portably; the residual window equals the engine's existing
  no-DBF-fsync durability).
- CDX/LMDB index reconciliation after a buffered commit/recovery (an indexed
  table needs a `REINDEX`) — this is why Consistency for the lane stays
  Unverified even though Atomicity/Durability are Partial.

## Scope discipline

`Partial` here is a scoped, evidence-backed gain, not a full-ACID claim. Full
ACID for the engine remains **Unverified**; concurrency/isolation and all
non-buffered and multi-store lanes are untested. Historical beta-0 is retained so
the improvement remains visible.
