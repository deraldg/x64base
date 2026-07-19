# Session Closeout — Table-Buffer Write-Ahead Log (durability)

```yaml
ai_report_audit:
  report_id: AIPR-20260719-003
  project: project.x64base.runtime
  branch: homegrown-cnx-20251112-branch
  baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  access_mode: local_write
  feature: table-buffer transaction write-ahead log (WAL) + crash recovery
  design: docs/maintenance/TABLE_BUFFER_WAL_DESIGN_2026-07-19.md
  scope:
    added:
      - include/cli/table_state.hpp        # BufferJournalInfo.fp/change_count; add_change -> int; journal_begin_commit; recover decl
      - src/cli/table_state.cpp            # .tbj writer, durable fsync, hex enc/dec, recover_table_buffer_journal, priority-returning add_change
      - src/cli/cmd_commit.cpp             # journal_begin_commit (marker+fsync) BEFORE the DBF apply loop
      - src/cli/cmd_use.cpp                # recover_table_buffer_journal on open
      - src/cli/cmd_replace.cpp            # journal_note_change with assigned priority
      - src/cli/cmd_calcwrite.cpp          # journal_note_change (was not journaling)
      - include/cli/table_write.hpp        # journal_entry.priority = assigned (was tb.next_priority)
      - src/cli/table_buffer.cpp           # TABLE BUFFER HISTORY ON|OFF; DBF-sidecar log path
      - src/cli/cmd_delete.cpp             # buffered DELETE (CHANGE_DELETE + D redo), write-through path unchanged
    removed:
      - src/cli/table_state.hpp            # stale duplicate of include/cli/ (was shadowing edits)
      - src/cli/table_write.hpp            # stale duplicate of include/cli/
  authorization_note: >
    Original changes only in D:\code\ccode on the existing branch. No branch
    created/switched/renamed; not applied to C:\x64base or GitHub. Enabled only
    under TABLE BUFFER PERSISTENT (RamJournal); default RamOnly behavior is
    unchanged. Correctness-critical durability path -- each phase built + proven
    on the host with a hash-bound teed transcript.
  stage: proven_by_teed_transcript
  proof_logs:
    - labtalk/proofs/runs/wal_phaseA_proof_teed_20260719T080435Z.log       # sha 938D4EC361EB34D8D7A3130E62ABDC06F8868DF3C75698C002F6FBE1A6292F60
    - labtalk/proofs/runs/wal_phaseB_verify_teed_20260719T081647Z.log      # sha 16B938E4A8DA362EFE54B15E022922210CAD9117232DCF6D227CDAC21D500C7A
    - labtalk/proofs/runs/wal_phaseC_proof_teed_20260719T082345Z.log       # sha FBA1FC92FA1CC531B8B54094D8BC644B1FA51DD13B35053D02775511A257EE54
```

## Problem

Table buffering, `COMMIT`, and `ROLLBACK` were **RAM-only**. `COMMIT` applied the
buffer straight to the DBF at commit time with no log and no `fsync` (only an
`fstream` flush); `ROLLBACK` dropped the in-memory multimap; there was no
recovery. A crash mid-`COMMIT`, or before the OS flushed, could leave the DBF and
the CDX/LMDB index inconsistent — the index (durable via LMDB) ahead of the data.
The journal hooks existed only as no-op stubs. (Full survey:
`TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`, "Current state".)

## What was built (three proven phases)

### Phase A — durable redo log on COMMIT / ROLLBACK  (sha `938D4EC3…`)
A real append-only `.tbj` writer with cross-platform durable sync
(`FlushFileBuffers` / `fsync`). Write-ahead ordering: redo appended during
`REPLACE`/`CALCWRITE`/`write_field`; on `COMMIT`, `journal_begin_commit` writes
the `C` marker and **fsyncs before** the DBF apply loop; the log is deleted after
apply; `ROLLBACK` discards it. Records are **full-fidelity** —
`U <recno> <priority> <H|S> <field>:<hex>` / `D <recno> <priority>` — one per
buffered write, so the multiple-retained-edits-per-field history is preserved in
the log, not collapsed to last-write-wins. Proof: `COMMIT` applied `Alpha2`,
`ROLLBACK` kept `Beta`, and with `TABLE BUFFER HISTORY ON` three edits to one
field were kept as three retained entries (seq 1/2/3) with `COMMIT` landing the
highest-priority `Edit3`.

### Phase B — crash recovery-on-open  (sha `16B938E4…`)
`recover_table_buffer_journal(area)` runs on `USE`: if `<dbf>.tbj` exists, it
replays the redo into the DBF (idempotent — `gotoRec`/`set`/`writeCurrent` /
`deleteCurrent`, matching `apply_one_recno`; append order == priority order, so
highest-priority wins) when a `C` marker is present, else discards it; then
removes the log. The log path is now the DBF sidecar. Proof simulated a crash:
setup left an uncommitted `U 1 1 S 2:<hex "Recovered">`, the runner appended `C 1`,
and reopening replayed it — `NAME=Recovered`, log removed.

### Phase C — DELETE routed through the buffer/log  (sha `FBA1FC92…`)
Under buffering, `DELETE` (single-record and scoped) stages a `CHANGE_DELETE`
and journals a `D` record, deferring the DBF mutation to `COMMIT` (or discarding
on `ROLLBACK`; replayed on recovery). Proof: buffered delete deferred, `COMMIT:
complete. (1 recs)` applied it, and a second buffered delete + `ROLLBACK:
discarded 1 change(s)` left the record live. The **buffer-off `DELETE` is
unchanged** — it keeps the write-through path with the Phase 1.3d batched index
(the buffered branch forks before it), so that optimization is not regressed.

## Preserved / not regressed

- **Multiple-retained-edits-per-field (history mode).** The buffer's `add_change`
  history/single logic is untouched; the WAL logs per write, so every retained
  edit is recorded with its priority and `H`/`S` mode. Added
  `TABLE BUFFER HISTORY ON|OFF` (the mode previously had no command).
- **Default (RamOnly) behavior.** All journal functions early-return unless
  `RamJournal` is active; non-persistent COMMIT/ROLLBACK are byte-for-byte as
  before.
- **Phase 1.3d batched-index DELETE.** Only the buffer-on path changed; the
  write-through path (and its chunked LMDB batching) is the default and untouched.

## Open items (documented, non-blocking hardening)

1. **DBF `fsync` after replay/commit.** `std::fstream` doesn't expose the OS
   handle portably, so the replayed DBF is flushed to the OS but not force-synced
   before the log is removed. The log is removed only after replay completes (a
   mid-replay crash re-recovers on next open), so the residual window equals the
   engine's existing no-DBF-fsync durability — not a regression, but the last mile.
2. **CDX/LMDB index reconciliation after a buffered commit.** `COMMIT` /
   recovery update the DBF but not the CDX index (COMMIT does no incremental CDX
   maintenance — pre-existing for buffered `REPLACE` too). An indexed table needs
   a `REINDEX` after a buffered commit/recovery. Same follow-up for buffered
   `DELETE`.
3. **Binary `.tbj`** is a later optimization; v1 is text for provability.

## Durability status (honest)

Committed table-buffer transactions are now **crash-recoverable** via the fsync'd
redo log — a real durability gain where there was none. This is scoped to the
table-buffer path; it does **not** claim full ACID (the engine's broader ACID
guarantees remain **Unverified** per `acid-and-glass-box`), and the two open
items above are the remaining gaps for full durability on indexed tables.
