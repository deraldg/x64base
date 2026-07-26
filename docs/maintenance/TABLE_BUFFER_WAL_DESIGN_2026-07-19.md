# Table-Buffer Write-Ahead Log (WAL) — Design

Goal: give DotTalk++ table buffering **durable, crash-recoverable** transactions.
Today COMMIT/ROLLBACK are RAM-only (see "Current state"); this adds a durable
redo log so a committed transaction survives a crash and an uncommitted one is
cleanly discarded.

## Current state (examined 2026-07-19)

- Buffer is a per-area in-RAM `TableBuffer` (`multimap<recno, ChangeEntry>`) in
  `src/cli/table_state.{hpp,cpp}`. Only `REPLACE` is buffered; `DELETE` is
  write-through.
- `COMMIT` (`cmd_commit.cpp`) applies the buffer to the DBF at commit time via
  `writeCurrent`/`deleteCurrent` — **no log, no `fsync`** (only `fstream` flush).
- `ROLLBACK` (`cmd_rollback.cpp`) drops the multimap.
- No `BEGIN/END TRANSACTION`, no recovery. LMDB (CDX index) is the only durable
  component, so the index can be ahead of the data after a crash.
- The journal hooks are **pre-placed as no-op stubs**: `journal_note_buffer_on`,
  `journal_note_change`, `journal_note_commit`, `journal_note_rollback`, a
  `BufferPersistenceMode {RamOnly, RamJournal}`, a `BufferJournalInfo`, and the
  intended `.tbj` extension. This design fills those in.

## The `.tbj` log — format (v1, text/line-based)

One append-only file per table, a **sidecar next to the DBF**: `<dbf-path>.tbj`
(so recovery-on-open can find it from the table identity). Text/line format for
v1 so it is inspectable and provable; a binary format is a later optimization.

```
TBJ1 <dbf-path>\n                          header (one, on open/begin)
U <recno> <priority> <H|S> <f>:<HEX> …\n   redo: set record <recno> field <f> = value (hex bytes)
D <recno> <priority>\n                     redo: mark record <recno> deleted
C <count>\n                                COMMIT marker (durable point; <count> records precede it)
R\n                                        ROLLBACK marker (optional; file is deleted anyway)
```

**Full-fidelity retained edits.** Every buffered write is one `U`/`D` record, so
the multiple-retained-edits-per-field capability is preserved in the log — three
edits to one field are three records, not a last-write-wins snapshot.
`<priority>` is the buffer's per-write priority (`add_change` returns it), and the
`H`/`S` flag records whether the edit is kept as **h**istory or folded to
last-write-wins (**s**ingle). So replay/audit can reconstruct the retained edits,
not just the final value. All three buffered-mutation paths journal this way:
`REPLACE` (`cmd_replace.cpp`), `CALCWRITE` (`cmd_calcwrite.cpp`), and the shared
`write_field` helper (`table_write.hpp`).

Field values are hex-encoded so arbitrary stored bytes (spaces, high bytes, NULs)
survive a line-based format. Redo is **idempotent** ("set recno's field to this
value" / "mark deleted"), so replay is safe to run more than once.

## Write-ahead protocol (the ordering that makes it safe)

1. **During the transaction** (`REPLACE`, later `DELETE`): append a `U`/`D` redo
   line to the log (buffered write). — `journal_note_change`.
2. **On COMMIT, BEFORE applying to the DBF**: append the `C <count>` marker and
   **`fsync`** the log (`FlushFileBuffers` on Windows / `fsync` on POSIX). Now the
   full redo set is durable. If this fails, abort the commit (keep the buffer).
   — `journal_begin_commit` (new; called before the apply loop).
3. **Apply** the buffered changes to the DBF (existing `apply_one_recno` loop).
4. **After apply succeeds**: `fsync` the DBF, then close + delete the log — the
   transaction is now fully durable in the DBF and the redo is no longer needed.
   — `journal_note_commit`.
5. **On ROLLBACK**: close + delete the (uncommitted) log. — `journal_note_rollback`.

## Recovery (on table open)

If `<dbf>.tbj` exists when the table opens:
- **has a `C` marker** → the crash happened between step 2 and step 4; the DBF
  apply may be incomplete. **Replay** every redo line into the DBF (idempotent),
  `fsync` the DBF, delete the log.
- **no `C` marker** → the transaction never committed (crash before step 2
  finished). **Discard** the log; the DBF is untouched (nothing was applied).

Idempotent redo + the single durable `C` marker give the standard
redo-WAL guarantee: **commit is atomic w.r.t. a crash** — all-or-nothing.

## Phases (each its own build + proof)

- **Phase A — durable writer + markers. DONE + proven (sha `938D4EC3…`).** The
  `.tbj` writer (append, `C` marker + `fsync` before apply, delete after;
  `R`/delete on rollback), hex helper, and cross-platform durable sync are
  implemented; `journal_note_change` is wired into `REPLACE`/`CALCWRITE`/
  `write_field`, and `journal_begin_commit` into `COMMIT`. Full-fidelity records
  carry `<priority> <H|S>`; `add_change` returns the assigned priority. Added
  `TABLE BUFFER HISTORY ON|OFF` (history mode had no command). Proof
  (`wal_phaseA_proof.dts`): COMMIT applied (`Alpha2`), ROLLBACK discarded
  (`Beta`), **history mode kept 3 retained edits for recno 1 (seq 1/2/3) and
  COMMIT landed `Edit3`**, `.tbj` created-then-removed cleanly, no crash under the
  fsync path. Also removed the stale duplicate `src/cli/table_state.hpp` /
  `src/cli/table_write.hpp` (the build uses the `include/cli/` copies).
  Deferred to Phase B: the DBF-sidecar log path (needs the open-time filename)
  and the DBF `fsync`.
- **Phase B — recovery-on-open. DONE + proven (verify sha `16B938E4…`).**
  Proof `run_wal_phaseB_proof_teed.ps1` PASSED: setup left `U 1 1 S 2:<hex
  "Recovered">` (no `C`); after appending `C 1` and reopening, `USE` printed the
  recovery notice, `recno 1 NAME = Recovered`, and the `.tbj` was removed.
  `recover_table_buffer_journal(area)` in `table_state.cpp`: on `USE`, if
  `<dbf>.tbj` exists, replay its redo (idempotent — `gotoRec`/`set`/`writeCurrent`,
  matching `apply_one_recno`; append order == priority order, so highest-priority
  wins) when a `C` marker is present, else discard; then remove the log. Wired
  into `cmd_use.cpp` after open. The log path is now the DBF sidecar
  (`journal_note_buffer_on` receives `A.filename()` via `area_dbf_filename`).
  Proof `wal_phaseB_setup.dts` + `run_wal_phaseB_proof_teed.ps1`: setup leaves an
  uncommitted `.tbj`, the runner appends a `C` marker (the crash-after-commit
  state), reopen replays → `NAME=Recovered`, log removed. **Deferred (hardening):
  the DBF `fsync` after replay** — `std::fstream` doesn't expose the OS handle
  portably; the log is removed only after replay completes (a crash mid-replay
  re-recovers on next open), so the residual window matches the engine's existing
  no-DBF-fsync durability, not a regression. Also open: index (CDX/LMDB)
  consistency after replay (a `REINDEX` reconciles).
- **Phase C — DELETE through the log. DONE + proven (teed sha `FBA1FC92…`).**
  Proof `wal_phaseC_proof.dts`: buffered `DELETE` reported `1 deleted` but
  deferred; `COMMIT: complete. (1 recs)` applied it; a second buffered delete +
  `ROLLBACK: discarded 1 change(s)` left recno 3 live (`NAME = Gamma`). Confirms
  deletes are transactional under buffering, with the write-through batched path
  unchanged when buffering is off.
  When `TABLE BUFFER` is on, `DELETE` (single-record and scoped) now stages a
  `CHANGE_DELETE` in the buffer and journals a `D <recno> <priority>` redo record
  (`buffer_delete_recno` / `delete_current_buffered_or_through` in
  `cmd_delete.cpp`), deferring the DBF mutation to `COMMIT` (`apply_one_recno`
  already handles `CHANGE_DELETE`) or discarding on `ROLLBACK`; recovery replays
  the `D` record. The **default (buffer-off) `DELETE` is unchanged** — it keeps
  the write-through path with the Phase 1.3d batched index, so that optimization
  is not regressed (the buffered path forks before it). Proof
  `wal_phaseC_proof.dts`: `COUNT DELETED` is 0 before `COMMIT` and 1 after; a
  buffered delete + `ROLLBACK` leaves the record live. **Caveat (same as buffered
  `REPLACE`):** a committed buffered delete updates the DBF but not the CDX/LMDB
  index (COMMIT does not do incremental CDX maintenance), so an indexed table
  needs a `REINDEX` after — tracked with the Phase B index-reconciliation item.

## Hook points (exact)

- Append: `journal_note_change` (`table_state.cpp`), called from
  `cmd_replace.cpp:848` (right after `tb.add_change`).
- Commit marker+fsync: `journal_begin_commit` (new), called in
  `cmd_commit.cpp` right after the `pending_before` snapshot, **before** the
  apply loop (`commit_one_area`, ~line 321).
- Commit finalize (delete log): `journal_note_commit` at `cmd_commit.cpp:383`
  (already positioned after apply).
- Rollback discard: `journal_note_rollback` at `cmd_rollback.cpp:75`.
- Recovery: table-open path (Phase B).

## Notes / constraints

- All original changes only in `D:\code\ccode` on the existing branch; nothing
  promoted. Correctness-critical; each phase gets a build + hash-bound proof.
- Enabled only under `TABLE BUFFER PERSISTENT` (RamJournal mode); default
  `RamOnly` behavior is unchanged (the journal functions early-return).
