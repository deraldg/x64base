# DotTalk++ ACID Assessment — beta-0

Status: Baseline educational assessment  
Verified: 2026-07-11  
Overall rating: **Unverified**

## Scope and claim

This baseline records hypotheses from the current design brief. It does not
claim runtime compliance. Engine source review, failure injection, and captured
test runs are still required.

> DotTalk++ currently demonstrates transaction concepts, but complete ACID
> guarantees have not been verified.

`COMMIT` and `ROLLBACK` are commands. ACID properties are observable guarantees.
The commands alone do not prove the guarantees.

## Visibility is not a defect or a guarantee

The educational viewer exposes pending changes, dirty/stale fields, and commit
state. That visibility does not weaken isolation. Isolation depends on what
other sessions can observe, which locks and versions are used, and how
conflicts are detected. Those behaviors still require concurrent-session
tests.

Likewise, a pending tuple-buffer change does not automatically make the
persistent DBF and index inconsistent. The risk boundary occurs when a direct
mutation or commit writes one participating store without maintaining or
recovering the others.

| Property | Rating | Current evidence | Missing evidence |
| --- | --- | --- | --- |
| Atomicity | Unverified | Table buffering supports rollback before commit; `COMMIT` reports per-record locking. The contract also admits that partial commit is possible. | Crash tests spanning DBF, memo, and index writes; coordinated recovery proof. |
| Consistency | Unverified | Dirty/stale state is visible. Buffer-only changes are not themselves persistent DBF/index divergence. `COMMIT` explicitly excludes CDX/LMDB rebuild. | Invariant tests after direct mutation, commit, and injected multi-store failures. |
| Isolation | Unverified | Buffered state and per-record commit locking mechanisms exist in source. | Concurrent reader/writer and multi-writer visibility, conflict, and lock tests. |
| Durability | Unverified | LMDB paths call transactional commit and memo stores expose flush operations. | Acknowledgement, reopen, and power-loss tests for every DBF, memo, index, and LMDB mutation path. |

## Lane matrix

| Lane | Baseline rating | Reason |
| --- | --- | --- |
| Buffered x64 mutation | Unverified | Buffer and rollback behavior needs captured runtime proof. |
| Direct `MULTIREP` | Unverified | Autocommit/non-transactional behavior has not been verified. |
| LMDB tag mutation | Unverified | LMDB-local transaction boundaries need source and runtime evidence. |
| DBF + LMDB combined | Unverified | No coordinated commit or recovery proof is registered here. |
| Memo + DBF combined | Unverified | Payload/reference crash recovery needs verification. |
| Legacy indexes | Unverified | No guarantee is inherited from the x64 lane. |

## Source-defined limits

- `COMMIT` documents `partial_commit_possible: yes`.
- `COMMIT` does not rebuild CDX or LMDB indexes.
- Persistent commit-journal and rollback-journal hooks are currently stubs.
- LMDB-local transactions do not prove a coordinated DBF + memo + index
  transaction.

These are mechanism observations, not substitutes for runtime proof. They
explain why the formal beta-0 rating remains `Unverified`.

## Rating gate

A lane/property rating may change only when its test result identifies the
mechanism, setup, expected observation, actual observation, and durable proof
artifact. A failure is evidence, not an embarrassment: it defines the next
engineering requirement.

## Next gates

1. Map mutation paths and flush boundaries in the engine source.
2. Capture rollback and validation-failure tests.
3. Add deterministic interruption points between DBF, memo, and LMDB writes.
4. Test reopen/recovery and invariant verification at every interruption.
5. Test concurrent sessions and document the actual isolation model.
6. Publish results in the versioned JSON evidence file.
