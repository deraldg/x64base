---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-080
  recorded_at_utc: 2026-08-20T03:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: 7156ac702
  authorization:
    requested_by: maintainer (member.derald), in-session -- "good , resume our
      mission", then "examine the ccode dir and find an appropriate home for our
      gui work", then "you are green to develop".
    scope: >
      Session closeout for AIF-120, run COWORK-20260818-001. Records the two
      rulings that landed (R70 grid-to-TupleStream binding, R71 lane-to-project
      promotion), the six corrections made, what is owed to other areas, the
      leftovers to delete, and the state the next session inherits.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_APPLICATION_UI_DSL_LANE_2026-08-20.md
    kind: session_closeout
---

# Session closeout -- AIF-120 (application-ui-dsl), 2026-08-20

**Start at `AI_README.md`, then `AI_PORTAL.md`. If you have not onboarded this
session, do that BEFORE reading anything below.**

That line is first on purpose. See section 5.

## Commits

Baseline for this session is `7156ac702`. The commits themselves are **not listed
here** -- see below for why. To read them:

```powershell
git log --oneline 7156ac702..
```

What is stable, and therefore stated, is which ruling lives in which document:

| Ruling | Document |
|---|---|
| **R70** -- the generated grid binds `DbTupleStream` | `AIF120_GRID_STREAM_BINDING_V1.md` |
| **R71** -- UIDEF promoted to `project.x64base.gui` | `AIF120_PROJECT_PROMOTION_V1.md` |
| **R72** -- the host contract read out of `run_shell()` | `AIF120_HOST_CONTRACT_V1.md` |
| **R73** -- `Order` is a mode, not an index format | `AIF120_ORDER_VOCABULARY_V1.md` |
| **R74** -- the frames render engine counts | `AIF120_RELATION_FRAMES_V1.md` |
| **R75** -- the refusal fixtures made reproducible | `AIF120_FIXTURE_CORPUS_V1.md` |

All six are **review-needed**; the author does not self-approve. Also landed: the
wx-samples correction, R73.3a, and the retirement of `wx_stream_harness.cpp`.

### Why there is no hash table here

This document carried one and it went stale **four times in one session** -- after
R72, after R73/R74, after R75, and after the retirement. Each fix was correct and
each was obsolete within the hour.

The house rule is *no perishable literals: if it can be cheaply measured, do not
assert it.* A hand-maintained commit table in a closeout is the definition of one,
and the proof is small and complete: staging the closeout WITH its ruling fixed the
staleness, and the row for that very ruling still had to read `(this commit)` --
because **a hand-written commit table cannot name its own commit.** The hash does
not exist until the commit is made, and the commit is made from the file. Being the
last commit is not sufficient either. Only a measurement closes it.

So the list is replaced by the command that produces it. The ruling-to-document
mapping stays, because that does not change after the fact.

## What was done

**R70 -- the grid gets its rows.** R67 declared `TupleStream` the `grid` kind's
runtime contract and then nothing constructed one. `uidef_wx.py --stream` now
builds a `DbTupleStream` from the same `BINDING` string the columns came from,
sets the order, and fills from `next_page(RowLimit)`. Built and **run**, not
syntax-checked: a wx binary linking 44 house translation units, filled from the
shipped x64 school tables, captured under Xvfb.

Running it is what earned the ruling. The first render showed three distinct
students against the *same* enrollment three times -- the document declared
`STUDENTS -> ENROLL ON SID`, the manifest checked it, the `tree` drew it, and
nothing had ever told the engine. No error anywhere in that path. Four more
defects fell out the same way. After the fix the three rows match
`DOTSCRIPT aif120/r70_stream.dts` character for character: the first time a
generated frontend and the house shell have answered the same question the same
way.

**R71 -- UIDEF becomes a project.** Not a decision I made: AIF-040 promotes a lane
that "spawns sub-lanes, gains an independent lifecycle, or becomes a program
others build under," and AIF-120 met all three before the question was asked.
`projects.yaml` roots four non-C++ products inside `ccode` -- including a
`kind: gui_project` -- and zero outside it, which answered the placement question
from the registry rather than from opinion.

**R72 -- the host was already written.** Added after this closeout first landed,
which is why the commit table above includes the closeout itself. The maintainer
pointed at `src/cli/shell.cpp`; `run_shell()` turns out to BE the host contract --
setup at 506-550, the stdin REPL at 551-769, teardown at 770-789 reversed. A GUI
replaces the middle third. `src/tv/foxtalk_app.cpp:469` was already hosting this
engine from a non-CLI frontend through the same `shell_engine()` seam. Reading it
convicted R70.5 of re-deriving `shell.cpp:532-534` per document, and corrected my
claim that selection-to-cursor had no mechanism -- `cursor_hook::set_callback` is
exactly that. `gui/uidef/wx_host.cpp` is the host; runtime-proven.

**R73 -- `Order` named a format the document does not choose.** Added after R72.
Asked to change `cnx` to `cdx` for x64, there was nothing to change:
`set_order_inx()` and `set_order_cnx()` are byte-identical and neither attaches an
index or selects a tag. Across four flavors of the MCC schema the engine reports
the formats each table offers, and **`INX` does not exist for x64** -- so contract
4c permitted a document to request a format the table cannot have. Now
`physical | ordered`, with the old spellings accepted and reported. It also
convicted R70: `set_order_*` returns void while `WORKSPACE OPEN` can say
`found (not attached)`, so a bound grid asks for an order, is told nothing, and
browses physical in silence.

**R74 -- the frames stopped rendering placeholders.** The maintainer's `REL ENUM`
demo showed match counts at every hop. `summary` had been rendering `ENROLL : n`
with a literal *n*; `relations_api` has had `match_count_for_child()` and
`list_tree_for_current_parent()` the whole time, under a comment reading
`// Debug / UI`. Now filled and measured live. The demo also showed a **second grid
shape** -- `enum_emit_for_current_parent` over a declared path -- that UIDEF cannot
express; recorded and deliberately not designed.

**R75 -- the leftover this session was carrying all along.** The maintainer asked
whether he could try his form and could not, which exposed that the eighteen UIDEF
documents every refusal count is quoted against were not in the repository. Four
regenerate from tracked author scripts; **the sixteen negative and property cases
existed only in this container.** `author_cases.py` reproduces them, verified
behaviourally. The reason nine rulings missed it is the finding: `cited-paths`
matches PATHS, and those fixtures are cited by NAME.

**Staged with this closeout, deliberately** -- the rule recorded below, applied on
its first opportunity.

## State

- `gui/uidef` -- 53 tracked files, renames preserved (git reported 95-100% similarity per file).
- `gui/README.md`, `labtalk/registries/projects.yaml` row `project.x64base.gui`.
- 251 citations retargeted across 55 documents; `cited-paths` reports **159 of 159 tracked, zero widows.**
- Six backends import and run from the new home; `KINDS` still 19; `generate(path, title, dispatch, stream)`.

## Owed, and to whom

| Item | Who |
|---|---|
| **MSVC verification of R70.** Everything is gcc 13 / wx 3.2.4 / Linux. R68's whole argument is that `long` differs LP64 vs LLP64, and R69 already cost a round of exactly this. I would not call the GUI attached until it links under MSVC | maintainer |
| **Naming: `gui/` vs `src/gui/`.** Both now exist; "the gui directory" is ambiguous. Consolidating `src/gui` under `gui/` touches `src/CMakeLists.txt:117,450,454` and was deliberately not bundled | owner ruling |
| **R71.1** -- `prepush_gate.py:380` documents the mass-ack as cmd.exe `set X=1 && git commit`; in PowerShell that sets a shell variable the gate cannot see | gate owner |
| **R70.6/.7/.8** -- three `-Wsign-conversion` in `include/xbase.hpp`; a stale "R70" citation at `db_tuple_stream.hpp:71` that means R69; `HELP TUPLE` documents `#n`, which the lexer deletes | engine lane |
| **BETA citations.** 26 across nine documents cite the BETA checklist as authority. The maintainer ruled it "a template"; `foxref.cpp` shows all 43 items `BetaStatus::OPEN`. Retarget to lane rulings | AIF-120, next session |

## Next unit

**Read this after R74.** This section has now been rewritten twice for the same
reason -- see the housekeeping note below.

- **Paging.** `next_page` is called once; the R74 fills also run once and nothing recomputes them when the cursor moves. R72 established `cursor_hook::set_callback` is the signal that should. One unit covers both.
- **A CMake target.** The 46-object link was assembled by hand from an `nm` closure.
- **The second grid shape**, when the owner rules on its document form. Runtime contract is `enum_emit_for_current_parent`.
- **MSVC.** Nothing in R70-R74 was built outside gcc 13 / wx 3.2.4 / Linux.
- **The positive half of R73** -- that ordered differs from physical -- needs a tree with the LMDB `.cdx.d` environments. This container has none.

Owner decisions open: `relations_boot::autoload()` and `cmd_INIT` participation
(R72); the `Path` grid form (R74); staging `x64.dts` and the 95 other untracked
`.dts` (R73.3a); and `gui/` vs `src/gui/` naming (R71).

## Corrections this session

Five, all recorded in their rulings. Two are worth repeating because they are the
same shape:

- **Correction 50** -- `--dispatch` and `--stream` did not compose; the dispatch branch assigned over the stream block. Found by asking whether they composed, not by anything failing.
- **Correction 51** -- my handoff ended in `git add docs/maintenance`. 967 paths staged, 199 data fixtures, 405 non-ASCII lines belonging to other lanes. I never wrote `-A` or `.`, which is the trap: **the rule is about breadth, not spelling.** `prepush-gate` caught it, nothing was committed, nothing was lost. `migrate_uidef.py` now emits the exact stage list it always knew.

## 5. Onboarding -- owed, and paid late

This session resumed from a compaction summary that opened with the work. Under
the portal's *"The onboarding instruction is the FIRST line, and onboarding
expires"*, that is a defective handoff -- and the duty is symmetric: a resuming
agent handed work without that line treats initiation as still owed. I did not. I
worked R70 to completion and onboarded only when the maintainer said to.

**The finding: a compaction summary is structurally defective by that rule every
time,** because a summary opens with state and task by construction. Two proposals,
both owner calls:

- a resuming agent should treat any compaction summary as a handoff missing its first line, and onboard before acting;
- lane session records should carry the onboarding directive as their literal first line, so it survives compaction. This document does.

## A closeout committed mid-session is a perishable literal

Recorded in the Commits section above, where it is demonstrated rather than
described. Short form: this document went stale four times in one session, the fix
is to measure rather than assert, and the deciding evidence is that a hand-written
commit table cannot name its own commit.

## Housekeeping

Gitignored, mine, safe to delete: `tmp/r70_eng.tgz`, `tmp/r70_src.tgz`,
`tmp/r71_stage_list.txt`, `tmp/_to_delete/r70_section4d.md`.
