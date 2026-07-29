# Codex Handoff -- Table-Buffer Visibility: Who Can See an Uncommitted Edit?

Date: 2026-07-29
Prepared by: Claude / Cowork (`member.ai.claude.cowork`), run `AIPR-20260729-001`, lane AIF-074
For: Codex (`member.ai.codex`)
Authority root: `D:\code\ccode`, branch `development`
Baseline commit for every citation below: `4a9ff7525` (later AIF-074 commits touch
`src/cli/sqlsel_statement.cpp` only and do not change the finding)
Status: `review-needed` -- a source-verified finding plus an **UNRUN** probe.
NOT a defect report, NOT an authorized change. The disposition is the owner's.

> **UPDATE 2026-07-29 -- PROBE HAS NOW BEEN RUN. Section 4 is superseded by
> section 4a below.** One prediction confirmed, one FALSIFIED, one new finding.
> The owner has since ruled (R18) and the resolution is implemented; this
> document is retained as the investigation record.

---

## 1. Why you are being handed this

The finding sits at the intersection of two subsystems: the table-buffer/COMMIT
machinery (yours -- AIF-069 EXPORT SDF work, and the buffer/WAL lanes) and the
new SQLSEL statement surface (mine -- AIF-074, landed today). It is small,
sharp, and touches durable-write behavior, so it should be decided deliberately
rather than absorbed into either lane by whoever happens to be editing.

I have deliberately NOT changed any behavior. What follows is what the source
says, what I predict the runtime does, and the resolutions I can see.

## 2. The finding, in one paragraph

Under `TABLE BUFFER ON`, a `REPLACE` is recorded in the table buffer and is NOT
written to the DBF until `COMMIT`. Exactly one code path in the tree overlays
those buffered values when reading: the tuple projection path. Its reader,
`get_buffer_override`, is **file-local to `tuple_builder.cpp`** (defined at :90,
used at :391) -- it is not exported, and nothing else calls it. Every other read
path -- `DISPLAY`, `LIST`, and all predicate evaluation via `DbArea` -- sees the
on-disk record. Therefore, while edits are buffered, a single session holds two
different truths about the same record, and a `SQLSEL SELECT ... WHERE` can
filter on the committed value while projecting the buffered one.

## 3. Source evidence (verified by read, not inferred)

| Claim | Citation |
|---|---|
| Buffered REPLACE does not touch the DBF | `src/cli/cmd_replace.cpp` contract: "When TABLE buffering is ON, REPLACE records a buffered field change and marks the field stale/dirty. When TABLE buffering is OFF, REPLACE writes immediately through DbArea storage." |
| Projection overlays buffered values | `src/cli/tuple_builder.cpp:391` -- `if (field1 > 0 && get_buffer_override(area0, recno, field1, ov)) val = ov;` under the comment "Overlay TABLE-buffered edits (preview)" |
| The overlay reader is private to that file | `get_buffer_override` defined `src/cli/tuple_builder.cpp:90`; a tree-wide grep finds no other caller and no header declaration |
| Predicates read through the area | `dottalk::expr::eval_bool_compiled(cp, A, ...)` evaluates against the area's CURRENT record (`include/cli/expr/value_eval.hpp:90`); no buffer consultation on that path |
| SQLSEL projects through the tuple builder | `src/cli/sqlsel_statement.cpp` calls `dottalk::build_tuple_from_spec` per row |
| Staleness is per-field and feeds commit | `include/cli/table_state.hpp:92-103` (`stale_bits[kWords]`, `mark_stale_field`); `src/cli/cmd_commit.cpp` `auto_reindex_if_needed` gates on `dottalk::table::is_stale(area0)` |

For context on what COMMIT already guarantees (and why nothing here should be
re-implemented): `cmd_commit.cpp` takes a per-record lock at commit time only,
captures pre/post index key snapshots via `xbase::index_hooks`, fsyncs the redo
log + COMMIT marker BEFORE applying to the DBF, commits the index bulk before
the journal's final marker, and must not call `BUILDLMDB`. That protocol is
proven and is not in question.

## 4. The probe (written, NOT yet run)

`dottalkpp/data/scripts/buffer_visibility_probe.dts` -- untracked at handoff
time; SANDBOX-only; mutating but self-cleaning (ROLLBACK then ERASE). It asserts
nothing: it records behavior in labelled blocks for a ruling.

```
./datarun.ps1 -CommandLines (Get-Content dottalkpp\data\scripts\buffer_visibility_probe.dts) *> bufvis_probe.txt
```

My predictions, recorded in advance so the run can falsify them:

- Block A (`DISPLAY`, `LIST` after a buffered CSCI -> MATH): shows `CSCI` (on-disk).
- Block B (`TUPLE BUFVIS.SID,BUFVIS.MAJOR`): shows `MATH` (buffered).
- Block C (`COUNT FOR MAJOR = "CSCI"` / `"MATH"`): both return 1 -- predicates read disk.
- Block D (the sharp one): `SQLSEL ... WHERE MAJOR = "CSCI"` returns a row whose
  MAJOR column PRINTS `MATH` -- a statement contradicting its own filter; and
  `WHERE MAJOR = "MATH"` finds only record 2, silently excluding the record the
  user just set to MATH.

If block D comes back otherwise, my reading of the split is wrong and this
handoff is void -- say so plainly rather than working around it.

## 4a. OBSERVED RESULTS (probe run 2026-07-29; transcript `bufvis_probe.txt`)

Fixture: rec1 `CSCI`, rec2 `MATH` on disk. `TABLE BUFFER ON`, then rec1 buffered
`CSCI -> MATH`, never committed. `TABLE BUFFER STATUS` confirms: 1 change, 1
unique recno, mode RAM.

| Block | Predicted | OBSERVED | Verdict |
|---|---|---|---|
| A `DISPLAY` rec1 | `CSCI` (disk) | `MAJOR = CSCI` | **confirmed** |
| A `LIST` | `CSCI` (disk) | rec1 `MATH`, rec2 `MATH` | **FALSIFIED -- LIST overlays the buffer** |
| B `TUPLE` | `MATH` (buffered) | `1 \| MATH` | **confirmed** |
| C `COUNT FOR MAJOR="CSCI"` / `="MATH"` | 1 / 1 (disk) | 1 / 1 | **confirmed -- predicates read committed** |
| D `SQLSEL ... WHERE MAJOR="CSCI"` | row printing `MATH` | `1 \| MATH` | **confirmed -- statement contradicted its own filter** |
| D `SQLSEL ... WHERE MAJOR="MATH"` | only rec2 | `2 \| MATH` | **confirmed -- the just-edited row was excluded** |
| D `SQLSEL COUNT(*) WHERE MAJOR="MATH"` | 1 | 1 | **confirmed** |
| after `ROLLBACK` | clean revert | `DISPLAY` `CSCI`; SQLSEL `1\|CSCI, 2\|MATH` | **confirmed -- rollback is clean** |

**Correction to section 2.** The phrase "every other read path" was wrong.
`LIST` overlays buffered edits as well; the overlay is NOT confined to
`TUPLE`/SQLSEL projection. The verified split is therefore:

- **Sees buffered edits:** `LIST`, `TUPLE`, and (before R18) SQLSEL projection.
- **Sees committed data:** `DISPLAY`, and every predicate path
  (`COUNT FOR`, and by the same evaluator `LOCATE`/`SCAN`/`SET FILTER`).

**WITHDRAWN (owner correction, same day): the "DISPLAY vs LIST inconsistency"
was not a finding.** `LIST` is a DEVELOPER tool and does not maintain cursor
control -- its own contract says so (`cmd_list.cpp`: "restores cursor position
best-effort", `cursor_restore: best effort`), and HELP names **`SMARTLIST`** the
"Preferred listing command for user-facing ordered output". Comparing `DISPLAY`
against `LIST` compares a user surface against a developer surface and proves
nothing about engine consistency. The probe used the wrong listing command.

**What that left open has now been probed. See section 4c.**

## 4c. PROBE v2 -- the user-facing surfaces (run 2026-07-29)

Script `dottalkpp/data/scripts/buffer_visibility_probe_v2.dts`; transcript
`labtalk/proofs/runs/20260729_aif074_buffer_visibility_probe_v2.txt`. Fixture:
rec1 `CSCI`, rec2 `MATH`, rec3 `HIST`. Buffered (uncommitted): rec1 value edit
`CSCI -> MATH`, and a DELETE on rec3. No predictions were stated in advance.

| Surface | Buffered VALUE | Buffered DELETE |
|---|---|---|
| `SMARTLIST` (display) | shows `MATH` -- **buffered** | rec3 still listed |
| `SMARTLIST FOR <pred>` | matches on `CSCI` -- **committed** | -- |
| `DISPLAY` | shows `CSCI` -- **committed** | -- |
| `SQLSEL SELECT` (post-R18) | `CSCI` -- **committed, self-consistent** | rec3 still listed |
| `EXPORT ... CSV` | file contains `1,CSCI` -- **committed** | rec3 still exported |
| after `ROLLBACK` | `CSCI` everywhere | clean revert |

**FINDING (confirmed, user-facing): `SMARTLIST` contradicts itself exactly as
SQLSEL did before R18.** `SMARTLIST FOR MAJOR = "CSCI"` returned record 1 -- the
predicate matched the COMMITTED value -- and then PRINTED `MAJOR = MATH`, the
buffered value. The inverse also holds: `SMARTLIST FOR MAJOR = "MATH"` shows only
record 2, silently omitting the record the user just edited to MATH. This is the
same defect shape, in the command HELP designates "Preferred listing command for
user-facing ordered output". It is NOT covered by R18, which scopes SQLSEL only.

Supporting detail: `EXPORT` writes COMMITTED values (`1,CSCI`), which is
defensible -- an export is durable data -- but should be stated in its contract
rather than left implicit. A buffer-DELETEd record is still listed by SMARTLIST
and SQLSEL and still exported; whether SMARTLIST renders the `*` buffered-delete
marker from `smartlist_output.cpp:115-118` could not be determined from the
transcript's column spacing and remains UNVERIFIED.

**Post-R18 standing: SQLSEL is now the only probed surface that agrees with
itself.** The R18 pattern -- projection and predicate must observe one source --
is the available remedy for SMARTLIST if the owner wants parity. Untested still:
the browsers, `RBROWSE`, and the TUI grid.

## 4b. Disposition -- ruled and implemented

`R18` (charter `docs/maintenance/SQLSEL_PLDC_LANE_V1.md`): TUP/TUPLE are preview
surfaces and may overlay uncommitted edits; `SQLSEL SELECT` is statement-scoped
and reads committed table truth until SQLSEL DML is promoted; projection and
WHERE within one statement must observe the same committed source. This is
resolution option 2 below. Implementation landed via
`TupleBuildOptions::overlay_table_buffer` (default `true`, preserving TUPLE
behavior) with SQLSEL setting it false, and the SQLSEL contract now states the
rule. Sections 5-8 are retained for the reasoning record.

## 5. Resolutions, costed. The choice is the owner's, not ours.

| # | Resolution | Cost | Consequence |
|---|---|---|---|
| 1 | **Statement-scoped consistency.** SQLSEL's WHERE consults the same overlay as its projection | export a buffer-override accessor from the buffer layer (it currently exists only as a file-local helper); teach the predicate path to use it for SQLSEL only | a statement always agrees with itself; read-your-own-writes, which is what SQL users expect. Widest blast radius -- touches predicate evaluation |
| 2 | **Committed-only reads.** SQLSEL ignores the buffer entirely, projection included | pass a "no overlay" option through `TupleBuildOptions`, or project without the builder | a statement can never contradict itself and never shows unflushed state. Cheapest and safest for v1. Contradicts SQL read-your-own-writes expectations |
| 3 | **Leave as-is, document the split.** TUPLE is explicitly a preview surface; everything else reports committed truth | contract wording only | zero code risk, but SQLSEL must pick a side in its `@dottalk.usage` block and say so, because today it silently straddles |

My lean, stated as a lean and not a recommendation to act on: **(2) for v1**, because
it needs no new plumbing and cannot emit a self-contradictory row, with (1)
revisited when SQLSEL DML lands at P5 and read-your-own-writes stops being
optional. But this is a semantics call about durable-write behavior and it
belongs to `member.derald`.

## 6. Boundaries for this handoff

- Do NOT change buffer, COMMIT, ROLLBACK, WAL, or index-hook behavior. Nothing in
  section 3 is alleged to be broken; the protocol is proven.
- Do NOT "fix" the split before the owner rules. Options 1 and 2 are mutually
  exclusive and both are defensible.
- Do NOT edit `src/cli/sqlsel_statement.cpp` without coordinating -- AIF-074 is
  active in it (see section 7).
- The probe is safe to run: SANDBOX paths, throwaway `BUFVIS` table, ROLLBACK
  before close, ERASE at the end.

## 7. Collision avoidance -- AIF-074 is live in adjacent files

Landed today on `development` (all gated, all green):

| Commit | Touches |
|---|---|
| a401c1470 | 8 early-SQL contracts demoted to `experimental`; dead alias headers removed |
| 12269891e | `src/cli/workarea_util.{hpp,cpp}` created; REL family re-pointed |
| c69a71ea2 / 80fc284f3 | `unique_registry`, `cmd_setunique`, `cmd_workspace` (dtschema KEY), `cmd_ersatz` (`tuple_identity_key`), `cmd_validate_unique` |
| 49f014c73 | `set_relations.{hpp,cpp}`, `cmd_rel.cpp` (scan-limit honesty, `REL SCANLIMIT`) |
| eae4b786d | `src/cli/expr/rhs_eval.cpp` (`.T.`/`.F.` lexing) |
| 9a30383d2 | `tuple_types.hpp`, `tuple_builder.cpp` (per-column type surface) |
| 38a9631fe / 336b61741 | `sqlsel_statement.{hpp,cpp}` created; `cmd_sql_select.cpp` dispatch + usage |

`tuple_builder.cpp` and `cmd_sql_select.cpp` are the likely contact points for
any resolution above. Claim your own AIF number before starting
(`python tools/coordination/session_coordinator.py claim-aif`), stage per-path,
never `git add -A` -- one working tree, several sessions.

## 8. What "done" looks like

1. Run the probe; attach the transcript to `labtalk/proofs/runs/` with the
   `YYYYMMDD_<lane>_<topic>.txt` convention (a transcript is evidence; a script
   is only a claim).
2. Record the OBSERVED behavior -- confirming or falsifying section 4 -- without
   changing anything.
3. Put the three options in front of `member.derald` with the observed evidence.
4. Only then implement the ruled option, with a regression that pins it:
   buffered REPLACE -> SELECT -> ROLLBACK -> SELECT, asserting the chosen
   semantics at each step.

## 9. Lane context you may want

- Charter and rulings (R1-R17): `docs/maintenance/SQLSEL_PLDC_LANE_V1.md`.
  R16 (orthogonality) and R16b (statements ignore session state) are the most
  relevant -- note the tension: a table buffer is arguably session state, which
  is an argument for option 2.
- Session closeout: `docs/maintenance/SESSION_CLOSEOUT_SQLSEL_P0_P1_2026-07-29.md`
- Proofs registered today: `labtalk/registries/proofs.yaml`, ids beginning
  `proof.sqlsel.` and `proof.engine.`
