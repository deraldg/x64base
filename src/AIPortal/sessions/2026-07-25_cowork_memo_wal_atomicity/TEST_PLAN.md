# TEST PLAN -- AIF-061 M1 memo durability ordering

Baseline `163cbefc2`. Package status: **proposed. Not compiled. Not run.**

## 1. Checks the AI actually performed

Static reading only. No build, no execution, no data touched.

| Check | Method | Result |
|---|---|---|
| Commit ordering | read `src/cli/cmd_commit.cpp` | `journal_begin_commit` at :369; `mm->flush` at :440. Memo flush is **after** the commit point. Confirmed. |
| Memo durability | `grep -c 'fsync\|FlushFileBuffers' src/memo/memostore.cpp` | **0**. `MemoStore::flush()` (:143) is `write_header_()` + `_fp.flush()`. No OS-level sync anywhere in the memo subsystem. Confirmed. |
| Memo write timing | read `include/cli/memo_field_store.hpp:61-105` | `build_x64_memo_stored_value` calls `store->update_text_id()` at REPLACE time -- **eager**, long before COMMIT. Confirmed. |
| DBF field content | read `cmd_replace.cpp:54, 928` | field stores the **decimal object-id**, not the text. Confirmed. |
| Sync mechanism available | read `memostore.hpp:129-130` | stream is `std::fstream` (no portable fd); `_path` member exists, so sync-by-path is viable. Confirmed. |
| WAL sync pattern | read `table_state.cpp:31-45` | `wal_durable_sync` uses `_fileno`/`_get_osfhandle` on a `std::FILE*`. **Not reusable** for the fstream; hence sync-by-path. Confirmed. |

**Explicitly NOT verified:** that the patch compiles; that `dynamic_cast` to `MemoStore` in
`memo_manager.cpp` is valid at that point (`MemoStore` may need an include there); that
`MessageId::CommitMemoFlushFailedText` is in scope at the new call site; that no other caller depends
on `flush()` remaining non-durable.

## 2. Checks recommended but not performed

### 2a. Build

```powershell
cmake --build build --config Release
```

Expect clean. **Most likely failures**, in order:
1. `memo_manager.cpp` missing `#include "memo/memostore.hpp"` for the `dynamic_cast`.
2. `<windows.h>` ordering in `memostore.cpp` (min/max macros, `NOMINMAX`).
3. `MessageId::CommitMemoFlushFailedText` not visible at the earlier point in `cmd_commit.cpp`.

### 2b. Non-regression (must pass before the new test matters)

```
dottalkpp> DO regression BBS_LANE
dottalkpp> DO regression <existing memo/commit specs>
```

Then re-run the WAL Phase A/B/C procedures from
`docs/maintenance/SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md`. **Phase B (crash recovery) must
still pass** -- this patch alters the commit path and Phase B is the guard on it.

### 2c. The new gate -- fault injection (THE test)

A clean commit proves nothing here; the defect only appears in the crash window. Required:

1. `USE` a memo-bearing table, `TABLE BUFFER ON`, `SET BUFFER PERSIST RAMJOURNAL` (or however
   `RamJournal` is selected).
2. `REPLACE NOTES WITH "durability probe"` -- a value large enough to exceed any stream buffer.
3. `COMMIT`.
4. **Kill the process between the WAL commit marker and the memo flush.** Pre-patch that window is
   real; post-patch the memo is already durable when the marker is written.
5. Reopen the table. Recovery replays the `.tbj`.
6. **Assert:** the record's `NOTES` resolves to `"durability probe"` -- not a dangling id.

To demonstrate the defect exists, run step 1-6 **against the baseline first** and observe the
dangling reference. A fix whose bug was never reproduced is not proven.

Suggested harness: a `SET` toggle or `#ifdef` abort point between `journal_begin_commit` and the DBF
apply, mirroring how Phase B simulated its crash (setup left an uncommitted record, the runner
appended `C 1`, reopen replayed it).

### 2d. Failure-path check

Make `durable_flush` fail (read-only memo file, or a forced-error toggle). **Assert:** COMMIT aborts,
prints the memo-flush message, leaves the buffer intact and dirty, and **writes no `C` marker** --
the `.tbj` must show no commit marker, so recovery discards it.

### 2e. Cost

Time `COMMIT` over N memo-bearing records before and after. One added fsync per commit is expected;
anything worse suggests the sync is firing per-record rather than per-commit.

## 3. Expected local results

- Build clean, possibly after the include fixes in 2a.
- Existing regressions unchanged.
- WAL Phase A/B/C still green.
- New fault-injection test: **fails on baseline, passes with the patch.** That inversion is the proof.
- One extra fsync per memo-bearing commit.

## 4. Fixtures and mutation safety

- Use a **sandbox** table created and `ERASE`d by the test (standards seed section 2). Never a live
  table -- this test deliberately kills the process mid-commit.
- The fault injection must be **build- or toggle-gated** so it cannot fire in a normal run.
- Nothing here touches `dottalkpp/data` production tables or the BBS store.

## 5. Rollback / non-promotion conditions

Do not promote if any hold:

- Build fails and the fix is not obviously a missing include.
- Any WAL Phase A/B/C proof regresses.
- The fault-injection test does **not** fail on baseline -- meaning the defect was mischaracterised
  and this patch is solving the wrong problem.
- COMMIT latency rises materially (suggests per-record syncing).
- Rollback is `git checkout` of the five files; no format or on-disk change is introduced, so no data
  migration is involved either way.

## 6. Proof rows on success

- `proof.wal.memo_atomicity` -> `runtime_observed`, citing the fault-injection transcript.
- Amend `proof.wal.dbf_record` notes to record that the commit path changed and Phase A/B/C were
  re-run.
- Commit the transcript under `labtalk/proofs/runs/` -- it is now un-ignored (AIF-062), and a proof
  row citing an untracked artifact is a note, not evidence.
