---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-091
  recorded_at_utc: 2026-08-20T22:15:00Z
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
      Session closeout for AIF-120, run COWORK-20260818-001. Records the twelve
      rulings that landed (R70 through R81, grid-to-TupleStream binding through
      the character-cell weight allocation), the six corrections made, what is
      owed to other areas, the leftovers to delete, and the state the next
      session inherits.
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
| **R70** -- the generated grid binds `DbTupleStream` | `docs/maintenance/AIF120_GRID_STREAM_BINDING_V1.md` |
| **R71** -- UIDEF promoted to `project.x64base.gui` | `docs/maintenance/AIF120_PROJECT_PROMOTION_V1.md` |
| **R72** -- the host contract read out of `run_shell()` | `docs/maintenance/AIF120_HOST_CONTRACT_V1.md` |
| **R73** -- `Order` is a mode, not an index format | `docs/maintenance/AIF120_ORDER_VOCABULARY_V1.md` |
| **R74** -- the frames render engine counts | `docs/maintenance/AIF120_RELATION_FRAMES_V1.md` |
| **R75** -- the refusal fixtures made reproducible | `docs/maintenance/AIF120_FIXTURE_CORPUS_V1.md` |
| **R76** -- the UIDEF document is a CMake source | `docs/maintenance/AIF120_CMAKE_TARGET_V1.md` |
| **R77** -- measured against a wx sample the lane did not author | `docs/maintenance/AIF120_SAMPLE_MEASUREMENT_V1.md` |
| **R78** -- the round trip carried the tree and lost PROPORTION | `docs/maintenance/AIF120_ROUND_TRIP_V1.md` |
| **R79** -- `Weight` and `Fill` added to `PROPS` | `docs/maintenance/AIF120_LAYOUT_WEIGHT_V1.md` |
| **R80** -- `Weight` needs free space; two backends had none | `docs/maintenance/AIF120_WEIGHT_BACKENDS_V1.md` |
| **R81** -- the character-cell backend owns its remainder | `docs/maintenance/AIF120_CELL_ALLOCATION_V1.md` |

All twelve are **review-needed**; the author does not self-approve. Also landed:
the wx-samples correction, R73.3a, the owner ruling that `ccode/gui` is the GUI
project and `src/gui` is for C++ GUI code, and the retirement of
`wx_stream_harness.cpp`.

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
existed only in this container.** `gui/uidef/author_cases.py` reproduces them, verified
behaviourally. The reason nine rulings missed it is the finding: `cited-paths`
matches PATHS, and those fixtures are cited by NAME.

**Staged with this closeout, deliberately** -- the rule recorded below, applied on
its first opportunity.

**R76 -- the document becomes a build input.** R70's 46-object link was assembled
by hand from an `nm` closure, which is a measurement, not a build.
`gui/uidef/CMakeLists.txt` runs the author script, generates the C++ and compiles it: 62
seconds clean, 66 translation units, a 2.27 MB binary, with the UIDEF document as
a CMake SOURCE. Extracting it hit the same silent parent globals AIF-118 recorded
for pydottalk -- a standalone target inherits nothing and says nothing about what
it did not inherit, so the failure is a link error three layers from the cause.
Twenty-nine of the files it compiles are owned by no library; that list is
explicit in the target rather than discovered again by the next person.

**R77 -- graded by someone else's homework.** The maintainer offered the two
parallel wx samples for dogfooding. Every UIDEF document to date was authored by
this lane, and **a language graded only on its own homework will pass.** Measured
against a screen the lane did not write: a word for about 90% of the controls,
independent corroboration of contract 4b(b) from outside the lane -- and no word
at all for NEGOTIABLE geometry, a sash the user drags. That gap is a CONCEPT, not
a missing control kind, which is the only kind of gap an unauthored screen finds.

**R78 -- the round trip, and the property nobody thought to name.**
`gui/uidef/author_mainframe.py` describes `src/gui/wx/main_frame.cpp` as a UIDEF document
and `gui/uidef/uidef_wx.py` generates it back: **47 records, 45 elements, ZERO refusals**,
carrying a `pageset` inside a `page` inside a `pageset` that no prior document in
this lane has nested, and it builds and runs against wx alone with no engine. What
it could not carry was PROPORTION. Measured, 33 sizer additions carry an explicit
proportion -- 20 fixed, 13 saying take the remaining space -- so the render is a
recognisable frame in which NOTHING STRETCHES. R12 ruled layout intent portable and
quarantined coordinates, and then the design table captured order and containment
and dropped the one property all four backends share.

**R79 -- `Weight` and `Fill`, shaped so the upgrade is an extension.** The
maintainer answered with "gold standard", and the house rule *go for gold unless
the cost is platinum* has a second half that decided the design: ship the gold
SHAPED so platinum is an extension. Both properties went into `PROPS` on the
CHILD, not a seventeenth field -- a column would be tidier and would change the
record length, every reader, both importers and every document ever authored.
Absent means 0 and false, so **all 18 fixtures generate byte-identical output**: a
layout property added to a layout language that provably moves no existing
document. Child-not-container is also what makes R77's sash an extension rather
than a rewrite, because a sash is two weighted children plus a movable boundary.

**R80 -- and the claim R79 made one ruling earlier.** R79 shipped a table
asserting all four backends carry both natively. Carrying the property into the
other three found that table half wrong -- not about the toolkits, which have the
mechanisms, but about this lane's backends: **`Weight` is a share of FREE SPACE,
and a container that sizes to its children has none.** The HTML form was
`display:inline-block` and the character-cell renderer never divided its width; in
both, correct CSS and correct intent would have been emitted and been INERT. That
is asserting from the shape of the thing instead of measuring it -- in a ruling one
turn old, about the property I was implementing. HTML fixed, Tk implemented and
reporting the ratio its boolean `expand` loses, character cell reporting the drop.

**R81 -- the backend that has to own the remainder.** R80 named the two-pass
`draw()` and this is it. Along a `row` the character-cell renderer now measures
natural widths, divides the slack by the declared weights and widens the glyphs.
The reason it earned a ruling is not the two passes: **a character grid divides a
DISCRETE resource,** which the three pixel backends never confront. 3:1 of ten
spare cells is 7.5 and 2.5 and somebody must own the halves -- wx, Tk and CSS hand
that to a toolkit; here there is none. So the rule was chosen and WRITTEN DOWN:
`floor(slack * weight / total_weight)` each, remainder one cell at a time in
ORDINAL order, arbitrary but deterministic and stated, because a renderer that
rounded differently on different runs would make one document mean two things.
Proven on arithmetic chosen not to come out even.

Filling a budget is the first thing this renderer has ever done that could
OVERFLOW one, and it immediately did, three times: a phantom two-column trailing
gap recorded after every row, a box overhead that was 2 where a container GRANTED
and 3 where it ASKED so every nesting level cost three columns nobody reserved,
and a `stretch()` that would have grown a combo past its own drop arrow. **None of
those were findable by R79 or R80** -- it took a renderer that USES its budget to
expose a renderer that mis-states it. And because R81 honours SOME weights, every
weighted child it will not resize is now named individually with its own reason,
since a partial honouring is exactly where a silent drop hides.

## State

- `gui/uidef` -- **57 tracked files**, renames preserved (git reported 95-100% similarity per file).
- `gui/README.md`, `labtalk/registries/projects.yaml` row `project.x64base.gui`, `gui/uidef/CMakeLists.txt`.
- 251 citations retargeted across 55 documents; `cited-paths` reports zero widows on every commit since.
- Four backends carry `Weight`; `KINDS` still 19; `generate(path, title, dispatch, stream)`.
- The corpus regenerates: `gui/uidef/author_cases.py` (16 refusal fixtures) plus five other author scripts, 22 documents in all.
- `gui/uidef/prove_r81.py` asserts the cell-allocation rule and exits non-zero if it ever stops holding.

## Owed, and to whom

| Item | Who |
|---|---|
| **MSVC.** Nothing in R70 through R81 has been built outside gcc 13 / wx 3.2.4 / Linux. R68's whole argument is that `long` differs LP64 vs LLP64, and R69 already cost a round of exactly this. R76's CMake target makes this one command now, and a FAILURE would be more useful than another green Linux build. **This is the oldest open item in the lane by several rulings** | maintainer |
| ~~**Naming: `gui/` vs `src/gui/`**~~ -- **CLOSED by owner ruling**: `ccode/gui` is the GUI project and `src/gui` is for C++ GUI code. The coexistence I recorded as a cost is the structure; nothing moves, and `src/CMakeLists.txt:117,450,454` is not a pending migration | resolved |
| **R71.1** -- `prepush_gate.py:380` documents the mass-ack as cmd.exe `set X=1 && git commit`; in PowerShell that sets a shell variable the gate cannot see | gate owner |
| **R70.6/.7/.8** -- three `-Wsign-conversion` in `include/xbase.hpp`; a stale "R70" citation at `db_tuple_stream.hpp:71` that means R69; `HELP TUPLE` documents `#n`, which the lexer deletes | engine lane |
| **R73.7** -- `AREA`/`DBAREA` report `Order: ASCEND` for an area whose `Active tag` is `(none)` and which lists physically, so the reported order cannot be trusted as state. Two attach paths, two outcomes, one word | engine lane |
| **R73.8** -- `STRUCT` prints `Tags : (none)` for `STUDENTS.cdx` while `SET ORDER TO FNAME` selects a tag out of that container and `USE` auto-attaches `SID` from it; `CDX INFO` on `TEACHERS.cdx` lists four. **Reported, not concluded** -- one `CDX INFO` with `STUDENTS` selected settles it | engine lane |
| **R82.4** -- `dottalkpp/data/workspaces/mcc_x64.dtschema` declares `tag=none` for all thirteen areas while `mcc_x32.dtschema` declares real tags (`BLDG`, `CLS_ID`, `CID`, `DEPT_ID`, ...). So R73.7's "no active order on x64" is not only the directory-scan door -- the shipped x64 workspace file itself declares no tags while its x32 twin does. An asymmetry between two files, not a design decision | workspace owner |
| **R82.1** -- the 50-slot `dottalk::paths::Slot` enum has three hand-maintained printers showing **13, 18 and 37** slots (`src/cli/cmd_init.cpp:286`, `dump()` in `src/cli/cmd_setpath.cpp`, `describe()` in `src/common/path_state.cpp`); `slot_name()` already covers the enum and none of the three iterates it. `DBF_X64` is set at init and consumed by `src/gui/core/session.cpp`, and a maintainer reading `INIT: Paths` cannot see it. Owner ruled: report, do not fix | engine lane |
| **R82.2** -- `docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md` cites `gui/core/session.cpp`; the file is `src/gui/core/session.cpp` and is tracked. A citation missing its `src/` prefix, not a missing file (R81.5) | workspace-manager lane |  <!-- cite-check:ignore -->
| **R81.1** -- **24** repo paths cited in `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` cannot be reached from a clone: 23 widows, all ON DISK and merely untracked, plus **one that is GITIGNORED** -- `.../DOCFLUSH-20260722-001/FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv`, which `git add` can never stage (R42.1). R73.3a's shape at dashboard scale. Not on the rows this session touched, and `cited-paths` is advisory, so nothing blocked | dashboard owner |
| **R81.2 -- and my own sweep under-counted it.** I reported 22 by grepping for a whitelist of extensions (`py md cpp hpp h txt yaml dts DBF png FPT`). The gate found 24, because the two I missed end in `.csv` and `.mjs`. **A search shaped by the objects you already have cannot find an object with a different schema** -- the house doctrine, applied to my own evidence-gathering rather than to someone else's code, and the second time this session a whitelist has been the defect. The gate's regex is the one to trust; mine was a convenience that quietly narrowed the question | AIF-120, recorded |
| **BETA citations.** 26 across nine documents cite the BETA checklist as authority. The maintainer ruled it "a template"; `foxref.cpp` shows all 43 items `BetaStatus::OPEN`. Retarget to lane rulings | AIF-120, next session |

## Next unit

**Read this after R74.** This section has now been rewritten twice for the same
reason -- see the housekeeping note below.

- **MSVC.** See the Owed table. One `cmake` configure-and-build of `uidef_wx_demo` answers it, and it is the oldest thing here.
- ~~**The positive half of R73**~~ -- **CLOSED.** The maintainer ran it on the device (this lane's container has no `LMDB/`, and `LMDB/x64` is 577 MB, over the staging cap). `USE teachers NOINDEX` reports `Order : NATURAL` and lists recnos 1..20 in sequence; `SET ORDER TO FNAME` lists 16, 57, 64, 103, 114, 6, 36, ... in FNAME order. Transcript at `docs/maintenance/evidence/AIF120_R73_ordered_vs_physical.txt`. **It also reopened the ruling one notch** -- see R73.6 below.
- **`Order` has no word for DESCENDING (R73.6).** The command after the proof was `DESCEND`, and the engine answered `Order: DESCENDING.` -- same tag, opposite direction. R73 closed the set at two by surveying `DbTupleStream`'s setters, which have no direction, and not the order state the engine reports. `Descending` is a second AXIS, not a third value, and whether it belongs to the document at all or to the workspace beside `tag=` is an owner decision. Contract 4e(a).
- **`Order: ASCEND` is not evidence an order is active (R73.7).** `WORKSPACE OPEN`'s directory scan attaches the container and selects NO tag; `USE` attaches and selects one. Both report `ASCEND`. The scan path is the one a generated frontend uses, which makes R73.1's "asks for an order, is told nothing, browses physical" the NORMAL case rather than an edge one. Contract 4e(b).
- **Paging.** `next_page` is called once; the R74 fills also run once and nothing recomputes them when the cursor moves. R72 established `cursor_hook::set_callback` is the signal that should. One unit covers both, and it is the largest piece of unfinished runtime behaviour in the lane.
- **Tk through `grid()` rather than `pack()`** -- carries the ratio Tk's boolean `expand` loses (R80 section 4). Needs nothing from anyone.
- **Character-cell COLUMN weight** -- needs a fixed canvas height the way HTML needed a sized form. The mechanism is written once already; what is missing is a height to divide, and inventing one is a decision about what a character-cell render IS.
- **`FLOW = grid` row/column growth** -- `AddGrowableRow`/`AddGrowableCol`, open since R79.
- **The second grid shape**, when the owner rules on its document form. Runtime contract is `enum_emit_for_current_parent`.
- **The 26 BETA citations**, still pointing at a template the maintainer has ruled is not authority.

Owner decisions open: `relations_boot::autoload()` and `cmd_INIT` participation
(R72); the `Path` grid form (R74); staging `x64.dts` and the 95 other untracked
`.dts` (R73.3a); and R77's NEGOTIABLE geometry -- the sash the design table has no
word for.

## Corrections this session

Six, all recorded in their rulings. Four are worth repeating because they are the
same shape -- and the shape is that a fix applied to one SITE is not a rule:

- **Correction 50** -- `--dispatch` and `--stream` did not compose; the dispatch branch assigned over the stream block. Found by asking whether they composed, not by anything failing.
- **Correction 51** -- my handoff ended in `git add docs/maintenance`. 967 paths staged, 199 data fixtures, 405 non-ASCII lines belonging to other lanes. I never wrote `-A` or `.`, which is the trap: **the rule is about breadth, not spelling.** `prepush-gate` caught it, nothing was committed, nothing was lost. `gui/uidef/migrate_uidef.py` now emits the exact stage list it always knew.
- **Correction 52** -- I pushed a whole file over the working tree and DESTROYED a `cite-check:ignore` marker I had added directly to that tree an hour earlier, then reintroduced the very citation the marker existed to suppress while writing the correction for it. The remedy is one line and it is now a standing constraint: **one authoritative copy.** Edit the working tree in place; do not keep a scratch copy and push it whole.
- **Correction 53** -- adding an `OnExit` override split `return true; } };` for EVERY document, so the byte-identical-without-`--stream` invariant failed on a purely COSMETIC change. That is the invariant doing its job; it is now split only when the document actually binds.
- **Correction 54** -- R70.3's unused-helper fix had been applied to ONE helper instead of made a rule, so two new helpers reintroduced the same defect on six of eighteen fixtures immediately. Every helper is now gated on its own caller list. Same shape as 49, 51 and 52: the fix that lands at a site instead of at the rule comes back.

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

## R81.3 -- R75's finding, in the document that records R75

`cited-paths` on the commit that carried this closeout reported **9 paths cited,
9 tracked**, and passed. This document names things by name 43 times. **Thirty-four
of them are bare names the gate cannot see** -- including all twelve `AIF120_*.md`
rulings, which are this document's entire INDEX.

That is R75's finding exactly: *a gate sees the shape it was built to see, and its
silence about a class of thing is not evidence the class is clean.* R75 is three
paragraphs above, in this file, written this session. A green `cited-paths` on a
closeout whose index is invisible to it is a gate reporting on 9 citations and
being read as reporting on 43.

Fixed here for the twelve rulings and the five tooling scripts -- they now carry
`docs/maintenance/` and `gui/uidef/`, so the index is checkable. The rest stay bare
on purpose: `STUDENTS.cdx` and `TEACHERS.cdx` are data the engine locates,
`tmp/*` is scratch that should not exist next week, and inventing a path to make a
gate happy is worse than a name the gate cannot check.

**The general form, and it is not fixed:** a bare filename is a citation with no
verifiable target, and this house's convention writes rulings that way in every
index table. R75 made the fixtures reproducible; it did not make the citations
reachable. That is a lane-wide convention question, not a defect in this document.

## A closeout committed mid-session is a perishable literal

Recorded in the Commits section above, where it is demonstrated rather than
described. Short form: this document went stale four times in one session, the fix
is to measure rather than assert, and the deciding evidence is that a hand-written
commit table cannot name its own commit.

## Housekeeping

Gitignored, mine, safe to delete: `tmp/r70_eng.tgz`, `tmp/r70_src.tgz`,
`tmp/r71_stage_list.txt`, `tmp/logrow.txt`, `tmp/flavors.tgz`, `tmp/flavors/`,
`tmp/cfg.tgz`, `tmp/aif120_probe.tgz`, `tmp/_to_delete/`.

`gui/uidef/generated/` and the 22 `.DBF`/`.FPT` fixture pairs stay untracked by
design -- they are DERIVED, and R75 made every one of them reproducible from a
tracked author script. That is the difference between a leftover and a build
product, and R75 is the ruling that had to learn it the hard way.
