---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260910-COWORK-203
  recorded_at_utc: 2026-09-10T23:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260910-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: a616863fe
  authorization:
    requested_by: owner (member.derald), in-session 2026-09-10 -- corrected the
      cross-table refusal ("is not refused by design, unplanned at the time.
      we got really good at this, so there are no vetos, it is the next logical
      step in our work"), answered four design questions, ran AIFgen to claim
      AIF-160 on lane multi-area-commit, instructed a prior-art sweep ("it is
      important you take another look at prior art, we often miss it"), and
      then said "do it".
    scope: |
      Lane charter for AIF-160 (multi-area atomic commit). DESIGN AND
      MEASUREMENT ONLY. No source change is authorized by this document.
      Write access exercised for this report:
        docs/maintenance/AIF160_MULTI_AREA_ATOMIC_COMMIT_LANE_V1.md
      NOT authorized here and named so it cannot be assumed: any edit to
      src/cli/sqlsel_statement.cpp, src/cli/table_state.cpp,
      src/cli/cmd_commit.cpp or src/cli/cmd_regression.cpp; any journal
      format change; any amendment to the AIF-159 intake row.
  report:
    path: docs/maintenance/AIF160_MULTI_AREA_ATOMIC_COMMIT_LANE_V1.md
    kind: lane-charter
---

# AIF-160 -- one decision that spans N journals. Lane charter V1.

    lane      : AIF-160 (multi-area-commit)
    claim     : coordination/aif/AIF-160.claim
    run       : AIFGEN-20260910-155043
    intake    : docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md
    owner     : member.derald
    steward   : member.ai.claude.cowork
    design    : claude/DESIGN_ONE_DECISION_THAT_SPANS_N_JOURNALS.md
    status    : CHARTERED. NOTHING IS BUILT. Four decisions taken, one
                recommended, and M0 below REOPENS one of the four on evidence.
    opened    : 2026-09-10
    baseline  : a616863fe

## 0. What this document is, and what it is not

It opens the lane and stages the work. **It authorizes no source change.**

It also does one thing a charter does not usually do: **it reopens a decision
the owner already took.** Section 3 is a measurement that was supposed to be
milestone one, turned out to be answerable by reading, and came back against
the choice. Recording that in the charter rather than discovering it in
implementation is the entire point of writing this before writing code.

## 1. Why the lane exists

`enlist_sql_transaction` refuses a second table
(`src/cli/sqlsel_statement.cpp:3335`):

```
one SQL transaction may modify one table; cross-table atomic commit is not available
```

**That refusal is a placeholder, not a ruling.** An earlier steward document
described it as "by design"; the owner corrected that on 2026-09-10 -- it was
**unplanned at the time**. Nobody weighed cross-table atomicity and rejected it.

The rule that produced, and the reason it is at the top of this charter rather
than buried in a finding: **a refusal message is evidence of a BOUNDARY, never
evidence of a RULING.** Four published surfaces now repeat that refusal and one
calls it intentional (section 6.3). One unplanned boundary became four
assertions because nothing in the pipeline distinguishes "we decided not to"
from "we had not got to it yet".

Two lanes are blocked on the one mechanism: SQLSEL transactions, and tuple
writeback rung 3 ("all owner tables at the same time"). Building it once serves
both.

## 2. The mechanism, in one page

Measured against the shipped WAL, not a sketch. Full derivation in
`claude/DESIGN_ONE_DECISION_THAT_SPANS_N_JOURNALS.md`.

**What ships today.** One journal per area, `<dbf>.tbj`, format `TBJ1`,
append-only redo, hex-encoded values (`src/cli/table_state.cpp`).
`journal_begin_commit(area0)` appends a `C <count>` marker and performs **one
durable sync before any buffered change reaches the DBF**;
`journal_note_commit(area0)` **deletes** the log. `recover_table_buffer_journal`
runs at **every `USE`**: replay iff a COMMIT marker is present, else discard.
`COMMIT ALL` (`src/cli/cmd_commit.cpp:847`) **loops** areas -- a sequence of
independent commits, not one commit, and it does not stop on a failure.

**So the COMMIT marker is the instant a change becomes true, and it is per
area.** A write spanning three tables is three independent commits. A crash
between them leaves two applied and one not, and **each journal recovers
correctly for its own table** -- every part consistent, the whole wrong.

**The shape that survives.** Recovery happens at `USE`, one table at a time, so
a group member opened alone must decide whether its span committed, and that
decision is **not local**:

- **PREPARE, per area.** Append the redo plus `P <group-id> <count>` instead of
  `C`, and sync. Any area failing to prepare aborts the group; no group decision
  is ever written and every `P` span is later discarded.
- **DECIDE, once.** One durable record naming the group id as committed, in a
  group log outside any area's journal. **That single sync is the instant the
  whole group becomes true.**
- **APPLY, per area**, exactly as today, then delete each log.
- **RECOVERY** gains one rung: `C` replays as now; `P` looks up its group id --
  found and committed, replay; absent, discard. A single-table `USE` consults
  the group log without opening any other table.

Two simpler schemes were rejected in writing and the reasons are load-bearing:
**presumed abort with no group record** (a crash mid-phase-2 leaves some areas
committed and the rest discarded, which is the non-atomicity being removed), and
**one spanning journal** (recovery on opening any member would replay the
others, so `USE` of one table opens three). The second is kept as the honest
fallback of last resort and section 3 does not resurrect it.

## 3. M0 -- THE MEASUREMENT THAT REOPENS DECISION 6.2

**Decision 6.2 chose a DBF catalog as the group log**, house pattern, like the
workspaces catalog table, with the fsync cost "explicit and accepted" and the note that
whether a DBF write can meet the durability requirement is **the first thing to
measure**.

It has been measured, by reading, and **the answer is no as things stand.**

### 3.1 The obstacle was already recorded six weeks ago

AIF-023 (`docs/maintenance/TABLE_BUFFER_WAL_DESIGN_2026-07-19.md`, and its
closeout `docs/maintenance/SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md`)
lists among its open hardening items a DBF `fsync` after replay or commit, and
gives the reason: **`fstream` does not expose the OS handle portably.**

That is confirmed in the header. `include/xbase.hpp:767`:

```cpp
    std::fstream _fp;
```

The DBF is an `fstream`. There is no portable route from an `fstream` to a
`HANDLE` or a file descriptor, so there is no portable route to
`FlushFileBuffers` or `fsync`. **A DBF write cannot today be made durable at the
moment it returns.**

### 3.2 And the capability the design needs is already shipped -- on a different handle type

This is the half that was missing from both the design and from AIF-023's own
framing. `src/cli/table_state.cpp:32`:

```cpp
static bool wal_durable_sync(std::FILE* fp) {
    if (!fp) return false;
    if (std::fflush(fp) != 0) return false;
#ifdef _WIN32
    const int fd = _fileno(fp);
    if (fd < 0) return false;
    const intptr_t h = _get_osfhandle(fd);
    if (h == -1) return false;
    return FlushFileBuffers(reinterpret_cast<HANDLE>(h)) != 0;
#else
    return ::fsync(::fileno(fp)) == 0;
#endif
}
```

The journal is a `std::FILE*`, C stdio, and **`FILE*` does expose the handle on
both platforms**. `journal_begin_commit` calls this on every commit. The house
already performs exactly the durable write this design's phase 2 requires, on
both Windows and POSIX, in shipped code that runs on every buffered commit.

**So the obstacle is not "this codebase cannot fsync." It is "the DBF is opened
through the one handle type that cannot."** AIF-023's sentence is true and
narrower than it reads, and 6.2 picked the file type it applies to.

### 3.3 Three routes, and a recommendation

**Route A -- flat append-only group log, `FILE*`, reusing `wal_durable_sync`.**
Durability is a solved, shipped problem. Cost: not readable by the ordinary
verbs, so inspection needs its own instrument.

**Route B -- DBF catalog as 6.2 chose.** Requires giving the DBF writer a
durable-sync path first, which means changing how `_fp` is opened or held across
the whole engine. That is AIF-023's open hardening item, it is valuable
independently, and it is **a larger change than this lane** -- a group-commit
lane would be paying for an engine-wide durability upgrade before it can write
its first record.

**Route C -- both, split by role.** The flat log is the AUTHORITY (durable,
`FILE*`, on the critical path); a DBF catalog is a PROJECTION rebuilt from it
for inspection and for graded arms, off the critical path.

**RECOMMENDED: Route C, with Route A as its first increment.** 6.2 fused two
requirements that separate cleanly -- **durability of the decision** and
**inspectability of the record**. Only the first is on the fsync path, and only
the second wanted a DBF. Splitting them gets the house pattern's inspectability
without putting an un-syncable file at the instant the group becomes true.

**NOT RULED. This is the steward disagreeing with a decision the owner took,
on evidence found afterwards, and saying so plainly rather than implementing
around it.** If the owner prefers Route B, the lane's first milestone becomes
the DBF durability upgrade and the schedule below changes shape.

## 4. M1 -- the format bump belongs to two lanes, not one

Phase 1 writes `P <group-id> <count>` where `C <count>` goes today. That is a
journal format change, and **AIF-061 already designed one.**

Its intake row specifies an `M <id> <len> <hex>` memo record written before the
referencing `U` record and replayed memo-first, under a **TBJ2 version bump that
still accepts TBJ1** -- closing, in its own words, COMMIT's disclaimer that it is
not atomic across DBF, memo and index. The header says the same in the tree:
`include/cli/table_state.hpp:141` scopes the log to DBF record writes and names
`docs/maintenance/AI_MEMO_WAL_ATOMICITY_LANE_V1.md`.

**Measured 2026-09-10: TBJ2 has not shipped.** `src/cli/table_state.cpp:296`
still writes the literal `TBJ1` header, and no source file in the tree mentions
TBJ2.

So two unbuilt lanes both want the next version byte, and whichever lands first
sets the compatibility rule for the other. **M1 is a joint decision, not this
lane's to take alone.** The cheap outcome is one bump defining both additions;
the expensive outcome is TBJ2 then TBJ3, with two acceptance matrices for
recovery to satisfy.

**Open, and genuinely open:** whether `P` is a version bump at all. A TBJ1
reader that meets an unknown leading token must not silently treat the span as
uncommitted-and-discardable when in fact it was prepared -- but discarding is
exactly what an old reader would do, and for a group whose decision was never
written that is the correct outcome. Whether that makes `P` backward-safe
without a bump is a recovery-semantics question and it is **not settled here.**

## 5. M2 -- group identity and the log's schema

Not designed. What the charter fixes:

- A group id must be unique across processes, not just across areas, because
  recovery reads a log another process wrote. The house has a precedent for
  process-scoped identity in `locks::current_owner()` (`host:pid:ms`) and a
  standing finding that identity has five authorities and the lock system asks
  none of them (AIF-144). **Do not mint a sixth.**
- The log needs a retention rule. A group id is consulted by recovery at some
  arbitrary later `USE`, so entries cannot be deleted the way `.tbj` files are.
  Unbounded growth is not acceptable and neither is deleting an entry some
  unopened table still needs. **This is the design's least-worked corner** and
  it deserves attention before any code.

## 6. M3 -- SQLSEL enlist becomes many

The first consumer, per decision 6.1: a statement names its tables, so the group
is declared rather than derived.

### 6.1 The concrete first edit

`src/cli/sqlsel_statement.cpp:3181`, `SqlTransactionState`, is **singleton
shaped**: one `area`, one `area0`, one `lock_acquired_here`, and three
**per-area** buffer-policy save/restore fields (`prior_buffer_enabled`,
`prior_history_enabled`, `prior_persistence`). Cross-table is therefore a
collection plus per-member policy restore, not a flag. `release_sql_transaction`
and `rollback_sql_transaction` both walk that state and both become loops.

### 6.2 Contention is already refused, in the same function

Decision 6.3 chose refuse-immediately. `src/cli/sqlsel_statement.cpp:3344`,
eight lines below the cross-table refusal, **already refuses** a table that
"already has buffered changes outside this SQL transaction". 6.3 extends a
shipped stance rather than inventing one, which is a better argument for it than
the one the design gave.

Still required and still unnamed: a **deterministic acquisition order**, so a
partial grab does not churn. Refusing immediately without one converts a
deadlock into a livelock.

### 6.3 Four published surfaces move together, and one arm goes red on purpose

The refusal sentence is a **required transcript fragment** in
`validate_sqlsel_dml_transaction` (`src/cli/cmd_regression.cpp:2612`). **The day
`enlist_sql_transaction` stops refusing, SQLSEL P5 fails** until the pinned
string is updated in the same change. That is the arm working: the refusal
cannot quietly disappear.

The other three, all of which assert the refusal to a reader:

- `include/sql_ref.hpp:196`
- `src/cli/sqlsel_statement.cpp:2500-2501`
- `src/cli/cmd_regression.cpp:711` -- "transactions intentionally refuse a
  second target table", which is the propagated "by design" the owner corrected.

## 7. M4 -- proving refuse-on-contention, with a harness that already exists

AIF-159 recorded that provoking a concurrently held record lock "needs machinery
that does not exist", because "the tree's one multi-process harness is PKDURABLE,
which is SEQUENTIAL BY CONSTRUCTION".

**There is a second one.** `src/tests/test_lock_protocol.cpp:371` (AIF-150,
`docs/maintenance/AIF150_ATOMIC_LOCK_PUBLICATION_FINDING_V1.md`) starts **two
real processes behind one start gate**, requires exactly one winner, verifies
the published owner from the parent while the winner holds, and requires
cleanup. That is the shape M4 needs.

**FIRST STEP, AND IT IS A CHECK NOT A BUILD: confirm G6 is wired to a build
target and runs today.** The build files were outside the reviewed set when this
was found, so its liveness is unverified. A harness that exists and is not built
is a harness that has to be revived before it can be extended, and that is a
different estimate.

## 8. M5 -- BEFORE triggers, gated on a ruling

**Recommended, not ruled: TWO-PASS -- all vetos fire before any area prepares.**

`claude/PLAN_TRIGGERS_DECISION_E_FIRE_POINT.md` 4.1 puts BEFORE at commit entry
immediately above `journal_begin_commit` and calls it "all-or-nothing per area";
`src/cli/cmd_commit.cpp:503` says the same in the tree -- that property comes
from the journal, "not a shortcut". Two-pass is that doctrine one level up:
all-or-nothing per GROUP.

The alternative, deferring triggers from phase 1, would need the contract to say
a grouped commit does not fire BEFORE triggers -- **a capability regression
against single-table commit**, which is a shape this house has paid for before.

Cost of two-pass: a veto costs one extra pass and no durable writes. Cost of
veto-at-prepare: a veto costs durable prepares that are then thrown away.

**The owner's "there are no vetos" was authorization to proceed, not a statement
about trigger semantics.** That was the steward's misreading, it was corrected in
session, and it is recorded here rather than quietly repaired.

## 9. What this lane will NOT deliver

Named so no one infers them from "atomic commit":

- **Whole-row atomicity for memo-bearing rows.** The DTX store is an append-only
  OBJECT store with its own id space and version lineage
  (`claude/FACT_WHY_MEMO_IS_THE_ONE_SPECIAL_CASE.md`), so a group commit can be
  atomic about the RECORD and not about the OBJECT the record points at. That is
  AIF-061's lane. **It must be stated in the contract, not discovered later.**
- **`partial_commit_possible` staying a single answer.** It becomes two-level:
  still yes per area inside a member's own apply, no for the group.
- **`COMMIT ALL` changing.** Decision 6.4: group commit is a NEW entry point.
  AIF-159 spent four commits protecting native `COMMIT` and `ROLLBACK` on the
  owner's instruction about the table-buffer student application; nothing native
  changes here.
- **Every write surface joining a group.** MULTIREP direct-writes
  unconditionally and is single-area (`src/cli/cmd_replace_multi.cpp:43` names
  AIF-151 as the upgrade), and bare `INSERT`/`UPDATE`
  (`src/cli/cmd_sql_insert.cpp`, `src/cli/cmd_sql_update.cpp`) write directly and
  fire nothing. **A group is only as atomic as the narrowest path into it.**
- **Index reconciliation.** AIF-023 leaves CDX/LMDB reconciliation after a
  buffered commit or recovery open, needing a `REINDEX`. A group multiplies it
  by N. Out of scope, and it is the next thing that will look like this lane's
  problem.

## 10. One correction owed elsewhere

AIF-159's intake row still states that the tree has one sequential multi-process
harness. Section 7 disproves it. **Amending a landed intake row is its own
decision and is not taken here**; this charter is the forward reference until
the owner rules on whether that row is amended or annotated.

## 11. Sequence

1. **M0 ruling** -- Route A, B or C for the group log. Blocks everything, and
   section 3 recommends C-via-A against decision 6.2 as taken.
2. **M1 joint decision with AIF-061** -- one version bump or two. Blocks any
   journal write.
3. **M4 first step** -- confirm the G6 harness builds. Cheap, and it sizes M4.
4. **M2** -- group id and retention. The least-worked corner.
5. **M3** -- SQLSEL enlist becomes many, with the four surfaces moving together.
6. **M5** -- gated on the 6.5 ruling.

Nothing after step 1 should start before step 1 is answered, because the group
log is the only new durable authority in the design and everything else writes
to it or reads it.

## 12. What is measured here and what is not

**Measured 2026-09-10 by reading the tree at `a616863fe`:** the WAL contract in
section 2; `wal_durable_sync` and the `FILE*` handle route; `include/xbase.hpp:767`
as an `fstream`; `TBJ1` still being the written header with no TBJ2 anywhere;
`SqlTransactionState`'s singleton shape; the second refusal at `:3344`; the
pinned transcript fragment at `cmd_regression.cpp:2612`; the `COMMIT ALL` loop
not stopping on failure; the G6 harness's existence.

**NOT measured, and not claimed:** that G6 is wired to a build target; that a
`FILE*`-based group log meets the durability requirement **at runtime** (the
technique is shipped, the group log is not, and a shipped technique is an
argument rather than a measurement); that any of this is built; that a
deterministic acquisition order has been chosen; that 6.5 is ruled; that the
gate scripts or the build files were read for this charter.

Ships **review-needed**. The author does not self-approve.
