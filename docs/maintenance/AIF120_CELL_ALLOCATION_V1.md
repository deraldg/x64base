---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-090
  recorded_at_utc: 2026-08-20T21:30:00Z
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
    baseline_commit: 851a664bd
  authorization:
    requested_by: maintainer (member.derald), in-session -- "good continue", taking
      the first item R80 section 7 named: the character-cell two-pass draw().
    scope: >
      Make uidef_text.py space-filling along a row so contract 5c Weight has a
      reading on the character-cell backend, and prove the remainder rule.
      Writes gui/uidef/ and docs/ only.
  report:
    path: docs/maintenance/AIF120_CELL_ALLOCATION_V1.md
    kind: ruling
---

# AIF-120 -- R81: the backend that has to own the remainder

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R80 shipped `Weight` into three backends and reported it DROPPED on the fourth,
naming the fix: a two-pass `draw()`. That is this ruling. Along a `row` the
character-cell renderer now measures the natural width of each child, divides the
slack by the declared weights and widens the glyphs. What makes this unit worth a
ruling of its own is not the two passes -- it is that **a character grid divides a
DISCRETE resource, and the other three backends never have to answer that
question.** 3:1 of ten spare cells is 7.5 and 2.5, and somebody must own the
halves. wx, Tk and CSS hand that to a toolkit. Here there is no toolkit, so the
rule had to be chosen, written down, and proven -- including on a case whose
arithmetic does not come out even.

## 1. The rule

> **`floor(slack * weight / total_weight)` cells each, then the remaining cells go
> ONE AT A TIME to the weighted children in ORDINAL order.**

Earliest-wins is arbitrary. It is also DETERMINISTIC and it is STATED, which is
the whole of the requirement: a renderer that rounded differently on different
runs would make one document mean two things. The rule is in the source at the
site that applies it, not only here -- a rule kept in a ruling and not in the code
is a rule the next reader has to guess.

## 2. Proof, on arithmetic chosen not to come out even

`gui/uidef/prove_r81.py` authors one row of three text fields weighted 3:1:1 into
a 94-cell budget, renders it, MEASURES the cells each field occupies in the output
and checks them against the rule computed a second time and independently -- so
the assertion is a check and not an echo of the implementation:

```
avail    94 cells for the row
natural  [12, 12, 12]  (+ 4 cells of gap)
slack    54 cells, weights 3:1:1 -- 54/5 is NOT whole
rule     [45, 23, 22]
rendered [45, 23, 22]

+- R81 --------------------------------------------------------------------------------------------+
|+-----------------------------------------------------------------------------------------------+ |
||[___________________________________________]  [_____________________]  [____________________] | |
|+-----------------------------------------------------------------------------------------------+ |
+--------------------------------------------------------------------------------------------------+
OK -- 94 cells allocated, remainder 2 given earliest-first
```

54 is not divisible by 5. `floor` gives 32/10/10 = 52, two cells are left over,
and they go to the first two weighted children in ORDINAL order -- so 3:1:1 of 54
becomes 33/11/10 and the row fills its budget **exactly**: 45 + 23 + 22 + 4 cells
of gap = 94. The script also refuses to pass if the three widths ever become
equal, because a case that no longer exercises the remainder is not evidence
about the remainder.

## 3. What it looks like on the real document

`MAINFRAME` -- the round trip of the house's own wx frame -- before and after:

```
R80  ||< Open Table >  < Refresh >  < Close Area >  Command  [__________]  < Run >   | |
R81  ||< Open Table >  < Refresh >  < Close Area >  Command  [_____________________________]  < Run > | |
```

`T_CMD` declares `Weight = 1` and is the only weighted control in that row, so it
takes all of the slack. That is the same intent the hand-written C++ expressed as
`command_toolbar->Add(command_, 1, ...)`, arriving at a target that has no sizers.

## 4. The defect the two-pass pass found in the one-pass renderer

Filling a budget is the first thing this renderer has ever done that could
OVERFLOW one, and it immediately did -- three times over.

**4.1 The phantom trailing gap.** Row placement advanced the cursor by
`len(glyph) + 2` and then recorded `maxc` from the advanced cursor, so every row
claimed two columns after its last child that no child occupies. Harmless while
nothing ever reached the edge; with a filled row it pushed the box border off the
canvas. `maxc` now excludes the trailing gap.

**4.2 `BOX_OVERHEAD` was a literal in four places and a different number in a
fifth.** A container grants its content `avail_w - 2` and then asks its own caller
for `innerw + 3`. Under content sizing the difference never showed, because
nothing was ever as wide as its grant. Filled, **every nesting level cost three
columns nobody had reserved**, and `MAINFRAME` is five levels deep. The grant and
the request are now the same named constant, and a child that exactly fills its
grant produces a box that exactly fills the parent's.

That is a bug R80 could not have found and R79 could not have found. It took a
renderer that USES its budget to expose a renderer that mis-states it.

**4.3 The combo would have grown past its own drop arrow.** `stretch()` grew the
`_` run of anything shaped `[...]`, and a combo is `[________ v]`, which is also
shaped `[...]` -- so it would have become `[________ v___]`. The narrower shape is
tested first, and the docstring says why, because the ordering is the fix.

## 5. What R81 does NOT do, said out loud per child

R80 reported drops in one lump per container. R81 honours SOME weights, and a
partial honouring is exactly where a silent drop hides -- so every weighted child
this pass will not resize is now named individually, with its own reason:

```
DROPPED Weight on LB_AREAS (list) in AREAP -- it sits in FLOW=column, which
  distributes along an axis this target measures in whole lines with no fixed
  height to divide (R81)
DROPPED Weight on MAIN (panel) in WORK -- it is drawn from its own content, not
  from a glyph this pass can widen (R81)
```

Three reasons, all real:

| the child | why it is not resized |
|---|---|
| in a `column`, `grid` or `free` parent | the flow axis is HEIGHT, a character row is exactly one line tall, and the canvas has no fixed height to divide |
| a container or a frame in a `row` parent | it is drawn from its own children or from `frame_block`, not from a glyph this pass can widen |
| in a row already at or past its budget | there is no slack |

Measured on `MAINFRAME`: **20 weighted children, 2 honoured, 18 named.** R80
reported 20 dropped. The number that got smaller is the number that matters, and
the number that stayed honest is the sum.

`Fill` gets no implementation and no helper here, and the file now says why in
place of the code: `Fill` stretches ACROSS the flow axis, and the cross axis of a
character row is one line tall. There is nothing to stretch into.

## 6. Blast radius

22 documents in the corpus rendered before and after, captured whole in
`docs/maintenance/evidence/AIF120_R81_before_after.txt`:

| | |
|---|---|
| **19 of 22 byte-identical** | including all 16 refusal fixtures |
| `MAINFRAME` | changed by design -- section 3 |
| `FLOWDEMO`, `TABDEMO` | boxes **two columns narrower**, and correctly so: 4.1's phantom gap was being drawn into every row-flow container in the corpus |
| `manifest.py --all MAINFRAME.DBF` | four profiles, unchanged: DERIVE 3 on tk, html and text, DERIVE 3 / REFUSE 7 on minimal |
| wx, HTML, Tk | untouched. Only `uidef_text.py` changed |

The two tightened renders are worth naming rather than burying: they are not a
regression this ruling accepted, they are R80-and-earlier output that had two
columns in it which no element occupied.

## 7. Contract

No new vocabulary. Section 5c is unchanged; this is the fourth backend arriving at
it. The backend table in R80 section 1 gains its last row:

| backend | can `Weight` mean something? | since |
|---|---|---|
| wx | yes | R79 |
| Tk | yes, ratio lost to a boolean `expand` | R80 |
| HTML | yes, when the form declares ORIGIN dimensions | R80 |
| **character cell** | **yes, along a `row`** | **R81** |

## 8. Open

- **Character-cell COLUMN weight** -- needs a fixed canvas height the way HTML
  needed a sized form. The mechanism is now written once and would be reused;
  what is missing is a height to divide, and inventing one is a decision about
  what a character-cell render IS, not a coding task.
- **Tk through `grid()` rather than `pack()`** to carry the ratio -- R80 section 4.
- **`FLOW = grid` row/column growth** -- unchanged since R79.
- **R77's negotiable geometry** -- unchanged, owner decision.
- **MSVC** -- unchanged, still the oldest open item in the lane.

## 9. Good Neighbor

| | |
|---|---|
| What changed | `gui/uidef/uidef_text.py` (two-pass row allocation, `BOX_OVERHEAD`, per-child drop reports); `gui/uidef/prove_r81.py` (new); `docs/maintenance/evidence/AIF120_R81_before_after.txt` (new); this ruling; ledger rows |
| Whose area | AIF-120. `src/` untouched; the other three backends untouched |
| Authorization | maintainer, in-session: "good continue" |
| How to verify | `python prove_r81.py` -- asserts and exits non-zero on failure. `python uidef_text.py MAINFRAME.DBF` for the widened toolbar and the 18 named drops. `xvfb-run python3.12 manifest.py --all MAINFRAME.DBF` for the profiles |
| How to undo | `git revert`. 19 of 22 renders are byte-identical either way; the other three are section 6 |
| Risk | low, and confined to one file. The behaviour is gated on a property no fixture sets; the two unweighted renders that moved, moved by removing columns nothing was in |

## 9a. R81.3 / R81.4 -- the gate could not see the project this lane was promoted into

**Added after this ruling landed**, from the gate's own output on the commit that
carried it.

**R81.3.** `cited-paths` reported **9 paths cited, 9 tracked** on a session closeout
that names 43 files. Thirty-four were BARE NAMES -- including all twelve
`AIF120_*.md` rulings, which are that document's entire index. A green about 9 was
being read as a green about 43. That is R75's finding (*a gate sees the shape it
was built to see*) inside the document that records R75. Eighteen citations
retargeted to full paths; gate-visible went 9 to 21.

**R81.4, and this one is larger.** The retarget moved five scripts to
`gui/uidef/...` and the count went up by 12, not 17. The gate's `ROOTS` tuple
(`tools/staging/check_cited_paths.py:29`) lists nine directories and **`gui/` is
not one of them.**

R71 promoted this lane out of `tools/uidef` into `gui/uidef` and **retargeted 251
citations into a directory the verifying gate does not scan.** That commit reported
`cited-paths: OK -- 159 of 159 tracked, zero widows` and R71 quotes it as evidence
the migration was clean. It was evidence about the 159 paths that had NOT moved.

Measured before the fix:

| | |
|---|---|
| `gui/` paths cited across tracked `.md` | **175 citations in 66 documents** |
| distinct `gui/` paths | 57 |
| invisible to `cited-paths` | **all of them** |
| cost of switching them on | **one advisory** -- `gui/core/session.cpp`, cited by `docs/maintenance/WORKSPACE_MANAGER_AND_GROUPS_DESIGN_V1.md`, not on disk and not tracked; another lane's document, reported not fixed |  <!-- cite-check:ignore -->

`'gui/'` added to `ROOTS`, with the reason in the source above the tuple rather
than only here.

**The shape.** R42 found that `git add` on a gitignored path is a silent no-op, so
a green gate was evidence about what was STAGED and not what was intended. This is
the same sentence with a different verb: **a green gate is evidence about what it
was configured to LOOK AT.** A project promotion moves files; nothing moves the
gates' idea of where files live, and no gate reports a directory it was never told
about -- silence is what a blind spot sounds like. Any future promotion under
AIF-040 should check the gate configuration as part of the move, and that belongs
in AIF-040 rather than here.

## 10. Handoff -- PowerShell, run in `D:\code\ccode`

**R78, R79 and R80 have not landed.** `HEAD` is still `851a664bd` (R77), so the
working tree carries four rulings at once, and two files carry more than one of
them: `uidef_wx.py` has R78.1's `pageset` fix AND R79's `Weight` emission, and
`author_mainframe.py` and the ledger have been written by all four. Splitting
those by path would produce commits whose messages do not describe their
contents, which is worse than one commit that says so. So this lands as one.

```powershell
git status -uall

git add gui/uidef/author_mainframe.py
git add gui/uidef/uidef_wx.py
git add gui/uidef/manifest.py
git add gui/uidef/uidef_html.py
git add gui/uidef/uidef_tk.py
git add gui/uidef/uidef_text.py
git add gui/uidef/prove_r81.py
git add docs/maintenance/AIF120_ROUND_TRIP_V1.md
git add docs/maintenance/AIF120_LAYOUT_WEIGHT_V1.md
git add docs/maintenance/AIF120_WEIGHT_BACKENDS_V1.md
git add docs/maintenance/AIF120_CELL_ALLOCATION_V1.md
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add docs/maintenance/evidence/AIF120_R78_roundtrip.png
git add docs/maintenance/evidence/AIF120_R79_before_after.png
git add docs/maintenance/evidence/AIF120_R81_before_after.txt

git status -uall

git commit -m "AIF-120: R78-R81 -- the round trip found the design table had no word for PROPORTION; Weight and Fill added to PROPS, carried into all four backends, and the character-cell one states its remainder rule because it divides discrete cells"
```

Sixteen explicit paths, no directory adds, well under the mass threshold. Every
one exists and none is gitignored -- checked with `git ls-files` and
`git check-ignore` before this block was written, which is R42's lesson.

The lane closeout and the AIF-006 dashboard row are stale by four rulings and are
the next thing to write after this lands -- not before, because a closeout
committed mid-session is a perishable literal, which this session has now
recorded twice.
