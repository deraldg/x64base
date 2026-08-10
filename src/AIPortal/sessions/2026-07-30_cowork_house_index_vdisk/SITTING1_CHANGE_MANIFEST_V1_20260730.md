# Sitting 1 Change Manifest -- index mutation seam (items E, C1, A)

**Date:** 2026-07-30
**Run:** `DECLARED-CAPABILITY-VALIDATOR-20260730` - **Author:** Claude (Cowork, local write) - **Owner:** `member.derald`
**Baseline:** `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`
**Authorization:** maintainer, explicit, for sitting 1 items E + C1 + A; C1 lock policy ruled "skip and report".
**Status:** `review-needed`. Dev-only, **unstaged, uncommitted**.
**Owning lifecycle:** DotTalk++ SDLC - lane: implementation - change class: **C2** (behavioral, cross-cutting index maintenance)
**Truth state:** source-defined. **Proof state:** syntax-only. **Next gate:** MSVC Release build + `REGRESSION ALL` + a new `.dts`.

---

## 1. Files changed

| File | Item | Lines | What |
|---|---|---|---|
| `src/xindex/index_manager.cpp` | A | +75/-15 | `apply_replace_snapshot` diffs `(tag, key)` and emits only changes; `!backend_` now returns success |
| `src/xbase/dbarea.cpp` | E | +18/-2 | `replaceFieldStored` stops discarding the `apply_replace` result; reports through `err` |
| `src/cli/cmd_replace.cpp` | E | +20 | Warns and marks the field stale on `true` + non-empty `err` |
| `src/cli/cmd_calcwrite.cpp` | E | +15 | Same check, same seam |
| `src/cli/cmd_validate_unique.cpp` | C1 | +78/-3 | `REPAIR` routes through `replaceFieldStored`; skip-and-report accounting |

No other files. Nothing staged. No build artifacts, no data fixtures, no branch operations.

## 2. New contract introduced

`DbArea::replaceFieldStored` gains a documented third outcome:

| Return | `err` | Meaning |
|---|---|---|
| `false` | set | record NOT written |
| `true` | empty | record written, index maintained |
| **`true`** | **non-empty** | **record written, index NOT maintained -- treat as stale** |

Callers that ignore `err` on a `true` return keep their old behavior exactly. `cmd_REPLACE` and `CALCWRITE` now honor it.

## 3. Behavior changes a reviewer must agree to

### 3.1 Failure semantics flip (intended)

`apply_replace_snapshot` previously returned "at least one operation succeeded". It now returns "no attempted operation failed". A **partial** index update -- some tags written, some not -- previously reported success and now reports failure. That is the case where you most want the field marked stale, so this is an improvement, but it is an observable change in failure scenarios.

### 3.2 The accidental self-repair is gone (intended, but it was load-bearing by accident)

`on_append` is an upsert, so the old delete-all/insert-all quietly re-inserted any index entry that had gone missing, on the next unrelated `REPLACE`. Diffing removes that: an unchanged tag is skipped, so a missing entry stays missing until `REINDEX`/`REBUILD`.

The trade is deliberate. Paying 2N index writes on every record edit is a bad price for an undocumented repair that also **concealed the failure it was repairing**. Item E now reports that failure instead. But if you were unknowingly relying on self-repair, this change will surface pre-existing index damage rather than cause it. That is worth knowing before the first run on real data.

### 3.3 `COMMIT` goes quiet in one case (correct, but it moves output)

A `CHANGE_DELETE` commit of a record with no indexable keys previously hit `any == false` and printed `CommitIndexFinalizeFailedText`. It is now silent. Any golden-output test on COMMIT will move.

### 3.4 `VALIDATE UNIQUE ... REPAIR` now takes a per-record lock

Consequence of routing through the funnel. Per the maintainer ruling, a locked record is **skipped and reported**, never silently rewritten and never aborting the pass. Two new report lines appear only when non-empty:

```
VALIDATE: REPAIR skipped N record(s) (locked or write failed) at rec: ...
VALIDATE: REPAIR wrote N record(s) whose index update failed; REINDEX/REBUILD needed. rec: ...
```

`REPAIR` on a large table will be slower than before.

## 4. Bug found in review and fixed before handoff

The first draft of item A kept `if (!backend_) return false;` while item E started reporting that `false` to the user. Because `ensure_manager()` attaches a manager permanently and `close()` clears only the backend, **any** area that had once run `LOCATE`/`FIND`/`SEEK`, or had `SET ORDER TO` issued, would carry an attached manager with a null backend for the rest of the session. Every later `REPLACE`, `CALCWRITE` and `VALIDATE UNIQUE ... REPAIR` on a table **with no index open** would have printed "index update failed" and marked the field stale.

Fixed at the root: no backend means no index to maintain, which is vacuous success. `src/xindex/index_manager.cpp`, with the reasoning in the comment so it is not "simplified" back.

This is exactly the class of defect the diff-then-report pairing creates: item A made a return value load-bearing that item E then surfaced. Neither change was wrong alone.

## 4b. Runtime evidence (added 2026-07-30, wsl-lean build)

Three items moved from source-evidenced to **runtime-evidenced** on the `wsl-lean` Linux build (Ninja, LMDB, no TV/WX).

**C1 -- `VALIDATE UNIQUE ... REPAIR` maintains the index.** Regression `VUREPAIR`:

```
VALIDATE: OK - field 'SID' is unique across 4 record(s). REPAIR updated 1 record(s).
Found at 3.                        <- SEEK 31, the NEW key, no REINDEX between
VUR_T2_seek_new_key_is_ZEBRA:.T.
Found at 2.                        <- SEEK 20, surviving duplicate
VUR_T3_seek_old_key_is_MILLER:.T.
```

**A -- the snapshot diff.** Regression `IDXDIFF`, both stated targets met:

```
BENCH-1 (indexed field)     before=4 after=4 emitted 1/1 skipped=6 tags=[-LNAME,+LNAME]
BENCH-2 (non-indexed field) before=4 after=4 emitted 0/0 skipped=8 tags=[]
```

**Phantom-tag fix (`setTag`).** Found by running the A benchmark, not by reading. The first `IDXDIFF` run reported `before=5 after=5 ... tags=[-NOTE,+NOTE] ok=yes` -- an index write against a field with no tag, succeeding. Cause chain, all source-confirmed:

1. `capture_delete_snapshot_for_current_record` enumerates **fields**, not tags.
2. `IndexManager::setTag` never validated the name and always returned true.
3. `CdxBackend::setTag` fell back to `mdb_dbi_open(..., MDB_CREATE)`, manufacturing an LMDB sub-database for any name handed to it.

So every field a record ever mutated silently became a tag DB. The `.cdx` tagdir said 4 tags while the env held 5; `BUILDLMDB` reads the container and rebuilt only the real 4, so the two structures diverged with the phantoms invisible to every listing. Behind it sits a hard ceiling: `cdx_backend.cpp:188` opens the env with `maxdbs=128` while `DOTTALK_MAX_FIELDS` is 256.

Fixed by removing the `MDB_CREATE` fallback from both branches of `CdxBackend::setTag` and converting the resulting throw to a clean `false` in `IndexManager::setTag`. Confirmed by `before=5 -> before=4` and the explicit guard trace:

```
[INDEX TRACE] setTag tag=NOTE fail=setTag: tag not found in index environment: NOTE
```

**Item A did not cause this defect; it reduced it and made it visible.** Under the old delete-all/insert-all, every field got a phantom database on the first `REPLACE`.

## 5. Verification actually performed

- `g++ -fsyntax-only -std=c++17` clean on all five files (`-DDOTTALK_HAS_XINDEX=1` for the two CLI files that need it).
- Independent source review of the full diff and **every** caller of both changed functions, which produced the section 4 bug plus four smaller corrections (unchecked `readCurrent`, uncounted `gotoRec64` failure, message-id ambiguity, and the section 3.2 disclosure).
- Zero em-dashes in added lines.
- `git diff --cached` empty; five modified files, nothing else.

**Not performed, and not claimable:** no MSVC build, no `REGRESSION ALL`, no runtime, no benchmark. Syntax-only is not proof. The sandbox is a Linux mount of a copy, so `repository_role_guard.py` blocks by design and the real gates are host-side.

## 6. Maintainer commands to reach the next gate

```powershell
cd D:\code\ccode
cmake --build build --target dottalkpp --config Release
.\datarun.ps1 -CommandLines 'REGRESSION ALL'
```

Expected evidence, in order:

1. **Build green**, MSVC Release, warning-clean on the five files.
2. **`REGRESSION ALL` green** -- parity. Watch `INDEX_X64`, `CURSOR` x32/CNX, `table_buffer.dts`, and anything asserting COMMIT output (section 3.3).
3. **Benchmark for A**, stated up front per Prove-the-Bottleneck-First: a one-field `REPLACE` on an N-tag CDX/LMDB table should drop from **2N** committed LMDB write transactions to **2**. Measure with `DOTTALK_INDEX_TRACE` or wall-clock over a `REPLACE ALL` loop, normalized within the run. **If the reduction does not appear, report why rather than accepting whatever number lands.**
4. **New `.dts`** (not yet written): `VALIDATE UNIQUE FIELD <indexed> REPAIR` then `SEEK` the new value hits and the old misses, with no `REINDEX` between. This is the C1 proof and it does not exist yet.

## 7. Still open from sitting 1

0. **`REGRESSION ALL` parity has not been run since the `setTag` change.** This is the highest-priority gap. `setTag` now fails where it previously auto-created, and `src/cli/order_iterator.cpp` calls it as `(void)im.setTag(spec.tag, &err2)` at five sites, discarding the result. Previously a missing tag was silently manufactured and the iterator carried on; now the call fails and the iterator proceeds against whatever tag was already active. That is more correct, but it is a behaviour change on a navigation path and parity must be demonstrated, not assumed.
0b. **The guard trace is noisy on a normal path.** `setTag tag=NOTE fail=...` now prints twice per capture for every untagged field on every edit. It is the expected path, not a failure, so it should be demoted below the trace threshold or reworded. Cosmetic, but it will read as an error to anyone running with the trace on -- and the trace is on by default (section 7 item 7).

1. ~~The C1 proof script is not written.~~ **Done and green** -- `validate_unique_repair_index_proof.dts`, registered `VUREPAIR`. See section 4b.
2. **Dedicated warning message id.** `REPLACE`/`CALCWRITE` reuse the hard-failure detail id for a success-with-warning. Text is prefixed so a human can tell, but a harness keying on the id would misread success as failure. Fixing it properly is a message-catalog addition, deliberately not smuggled into this slice.
3. **`present_in` is O(N^2)** in field count (`index_manager.cpp`). Negligible at 20 fields, ~60k string compares per record on a 250-field table. Still far cheaper than 2N LMDB transactions. Switch to a sorted or hashed lookup if a wide table ever matters.
4. **`capture_delete_snapshot_for_current_record` swallows exceptions** and returns an empty snapshot indistinguishable from "no indexed fields" (`index_manager.cpp`). Pre-existing, but item E made the return value load-bearing, so a partially-failed capture can now report success while leaving orphan entries. Worth its own fix.
5. **`xbase::replaceFieldStored` free function** declared in `include/xbase_cli.hpp` has no definition anywhere in `src/`. Pre-existing and unrelated, but its doc comment describes exactly the TABLE ON/OFF wrapper that `cmd_replace.cpp` and `cmd_calcwrite.cpp` now open-code. A link error waiting for its first caller, and a candidate `AIF-079` D1 instance.
6. **Pre-existing em-dashes** at `src/cli/cmd_replace.cpp:10` and `:590`, untouched by this slice. Separate cleanup pass.

## 8. Delivery note

Local-access AI: original work in `D:\code\ccode` only, scoped to the authorized items, nothing staged or committed, dirty and untracked maintainer work preserved, no branch operations. Stage reached: **Dev only.** Not promoted, not published.
