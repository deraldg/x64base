# Memo / WAL Atomicity -- Closing the Last Store (Lane V1)

**Status:** design-intended -- not started. **Lane:** AIF-061 (continues run AIPR-20260725-001).
**Owning project:** `project.x64base.runtime`. **Evidence class:** `design-intended`.
**Depends on:** the shipped TABLE BUFFER WAL (`src/cli/table_state.cpp`) and `SET INDEXTXN`.

## Summary

x64base has **write-ahead logging with crash recovery for DBF record writes**. It is real, correctly
ordered, and already in the build. It does **not** cover the memo store. This lane closes that gap so
a memo-bearing row commits or does not commit, whole.

## What already exists (do not rebuild it)

`src/cli/table_state.cpp` implements a per-area redo log. Surveyed 2026-07-25:

- **Log file:** `<dbf>.tbj`, a sidecar so recovery-on-open can find it without a catalog.
  Truncated at buffer-on -- **one log per transaction**, not a growing global log.
- **Format `TBJ1`:**
  ```
  TBJ1 <table>
  U <recno> <priority> <H|S> <field>:<hex> [<field>:<hex> ...]
  D <recno> <priority>
  C <change_count>
  ```
  Values are hex-encoded so arbitrary stored bytes survive the line-based format. `<priority>` and
  the `H|S` flag preserve **retained edits**, so replay and audit can reconstruct the sequence of
  writes, not merely the final value. That is more than a redo log strictly needs and it is a real
  asset -- keep it.
- **Ordering (the write-ahead invariant, correct today):** `journal_note_change()` appends without
  syncing; `journal_begin_commit()` writes the `C <count>` marker and performs **one**
  `wal_durable_sync` (`FlushFileBuffers` on Windows, `fsync` on POSIX) **before** any buffered change
  is applied to the DBF. A failed sync returns false and the caller must abort. One fsync per
  transaction, not per change.
- **Recovery:** `recover_table_buffer_journal()` runs on table open. A log carrying the `C` marker is
  replayed idempotently ("set recno's field to this value" / "mark deleted"); a log without the
  marker is discarded; the log is then removed. Safe to call on every `USE`.
- **Gated by** `BufferPersistenceMode::RamJournal`. Every hook is a no-op returning true in other
  modes, so callers invoke them unconditionally.

**This lane adds a payload type to a working protocol. It does not invent a protocol.**

### Correction recorded

Until 2026-07-25 the header `include/cli/table_state.hpp` labelled this section
*"Persistent buffer / journal stubs"* and the hooks *"intentionally no-op placeholders."* Both were
**stale by several milestones** -- the implementation below them was real. An AI partner surveying the
header (correctly, per the survey-first rule) concluded x64base had no WAL and reported that to the
maintainer, who corrected it from memory. The comments are fixed and now state the real behavior and
the real gap.

This is the failure mode the `@dottalk.*` contract family exists to prevent, appearing in a header
comment rather than a contract block: **documentation that understates a shipped capability makes it
invisible to exactly the readers who were told to trust the docs.** Worth a standards-seed line: when
a placeholder becomes an implementation, the comment above it is part of the change.

## The gap

An x64 memo `REPLACE` converts text to a **stored object-id**, and the DBF field holds that id
(`src/cli/cmd_replace.cpp`: *"X64 memo text is converted into stored object-id text before DBF
storage"*). The WAL journals **field values**, so it captures the id -- never the memo content.

Failure sequence:

1. `REPLACE NOTES WITH "..."` -- memo store allocates/writes object O, field gets id(O), buffered.
2. `COMMIT` -- `.tbj` gets `U <recno> ... NOTES:<hex of id(O)>`, `C` marker, fsync. **Durable.**
3. Crash before or during the memo store's own durable write of O.
4. Recovery replays the `.tbj`. The record is restored **pointing at O**. O may be absent, partial,
   or stale.

Result: record-level atomicity holds; **row-level atomicity does not** for memo-bearing rows. The
recovered database is internally inconsistent in a way the WAL cannot detect, because from the log's
point of view the transaction committed cleanly.

The severity is bounded -- it needs a crash inside a narrow window on a memo write -- but the
consequence is a dangling reference that surfaces later as a read error, not at recovery time. Silent
inconsistency is worse than a loud one.

Index is **not** in the same position: LMDB provides its own ACID guarantees and `SET INDEXTXN ON`
already ties index maintenance into COMMIT. Index is a coordination problem (below); memo is a
coverage problem.

## Design

### M1 -- journal the memo payload (the core fix)

Extend the `TBJ1` format with a memo record, written **before** the `U` record that references it:

```
M <object-id> <byte-length> <hex payload>
U <recno> <priority> <H|S> <field>:<hex id> ...
```

- Replay order becomes: materialize memo objects, then apply record changes. The reference is
  therefore always satisfied at the moment the record is written.
- Idempotent by construction -- writing object O with the same bytes twice is a no-op.
- The single-fsync discipline is unchanged: `M` lines are appended alongside `U` lines and covered by
  the same `C` marker and the same sync.
- `cmd_replace` already declares `writes_memo` and `clears_memo_field` as effects, so the call sites
  that must emit `M` records are **already identified** by the usage contract. Use that, do not
  rediscover them.

**Open question for the maintainer:** large memos in a line-based hex log double the byte cost and
could dwarf the record payload. Options: (a) accept it, simplest and matches the format's existing
character; (b) length-prefixed binary section after the text header; (c) `M` records reference a
staged side-file for payloads over a threshold, with the log carrying the id plus a digest. Prefer
(a) until a measured problem exists -- the format's readability has been worth something.

### M2 -- version the format

Bump to `TBJ2` when `M` records may appear. Recovery accepts `TBJ1` (record-only, current semantics)
and `TBJ2`; a `TBJ1` log is still valid and replays as it does today. Additive and version-gated, in
the same style as the `ai-report-audit-v2` envelope.

### M3 -- clears and deletes

`clears_memo_field` must journal the clear, and record `DELETE` must not orphan memo objects the row
owned. Decide explicitly whether memo objects are reference-counted or garbage-collected, and record
the decision -- this is where a half-fix rots.

### M4 -- coordinate with the index

With memo covered, one transaction spans three stores: DBF (`.tbj`), memo (`.tbj` after M1), and
index (LMDB, own ACID). The current ordering -- WAL durable, then apply -- generalizes to two-phase:

1. `.tbj` durable (record + memo). **Commit point.**
2. Apply to DBF and memo store.
3. LMDB index txn commit.

A crash after step 1 is fully recoverable. A crash between 2 and 3 leaves the index stale relative to
the data, which is **already** the recoverable case today (indexes are derivable -- the whole
`**/*.cdx.d/` gitignore rests on that). Make that ordering explicit and documented rather than
incidental.

### M5 -- prove it

A regression that is **not** satisfied by a clean run:

- Commit a memo-bearing row with the journal on; assert `.tbj` carries an `M` record for the payload.
- Simulate a crash between WAL sync and memo apply (fault injection, or apply-phase abort); reopen;
  assert the memo content is present and the record resolves.
- Assert a `TBJ1` log still replays under `TBJ2` recovery.
- Register in `kRegressionSpecs` alongside `BBS_LANE`, self-asserting and sandboxed.

Promote `proof.wal.memo_atomicity` to `runtime_observed` only after the crash-window case is
**observed**, not merely coded. A WAL that has never been tested against an actual interrupted commit
is a design, not a guarantee.

## Non-goals

- Multi-table / cross-area transactions. Each area keeps its own log. Distributed commit across areas
  is a separate, larger question.
- MVCC or reader isolation. The existing lock discipline stands.
- Replacing the retained-edit (`H`/`S`, priority) semantics. Preserve them.

## Why this is worth doing

With memo covered, x64base has **atomicity and durability across every store it owns**, and the
honest description of the engine changes from "buffered writes with record-level recovery" to "an
ACID single-user embedded database in the xBase lineage." That is a materially different claim, it
is defensible from the source, and the remaining distance is one payload type plus a proof -- not a
new subsystem.

It also removes the last item on the `COMMIT` contract's own disclaimer: *"COMMIT is not an atomic
transaction across DBF, memo, and index storage."* Being able to delete that sentence honestly is the
lane's finish line.

## Ties

- `src/cli/table_state.cpp` -- the WAL this extends.
- `src/cli/cmd_commit.cpp` -- the contract disclaimer this lane retires.
- `src/cli/cmd_replace.cpp` -- `writes_memo` / `clears_memo_field`, the call sites to instrument.
- `SET INDEXTXN` (`src/cli/cmd_set.cpp`) -- the index half of M4.
- `docs/ai-friendly/AI_RUN_TRACEABILITY_LANE_V1.md` -- additive version-gating precedent.

Owner: `member.derald`. Steward: `member.ai.claude.cowork`. Evidence class: `design-intended`.
