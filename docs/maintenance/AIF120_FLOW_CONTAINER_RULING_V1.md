---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-030
  recorded_at_utc: 2026-08-19T09:55:00Z
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
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 9696b9692
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just woke up an hour ago ---
      go go go!" -- taking the fourth item in the queue: the `row` and `column` flow
      inferences that had never been rendered.
  report:
    path: docs/maintenance/AIF120_FLOW_CONTAINER_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R23: `FLOW` belongs to the container, and `grid` never said where it wraps

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

The open item was small: "`row` and `column` inferences never rendered -- 21 and 3
classifications." Rendering them found a defect in the reference consumer, a gap in
the contract, and an error in R19's own measurement.

## 1. R23.1 -- the reason they had never rendered

The contract's field table says `FLOW` is **"P on containers"**, and section 5 says
it plainly: *"A container declares a `FLOW`; its children declare `ORDINAL` and
optionally `SPAN`."*

`gui/uidef/uidef_tk.py` read `FLOW` off **the child being placed**:

```python
flow = (r['FLOW'] or '').strip().lower()      # r is the CHILD
...
elif flow == 'row':
    w.pack(side='left')
```

No importer writes `FLOW` onto a child -- `import_scx.py` sets it on `form`,
`container` and `pageframe` only. So that branch could never fire. `row` and
`column` had not merely gone untested; **they were unreachable.**

`docs/maintenance/evidence/AIF120_flow_ab.png` is one document rendered twice. A
is the committed consumer: four buttons in a `FLOW = row` panel stacked vertically,
and the two-column grid laid out as a single stack. B is the same table after the
consumer reads `FLOW` from the container: the row is a row, the grid is a grid, and
the spanning control occupies both cells.

The document, `gui/uidef/author_flow.py`, exercises all four values --
`row`, `column`, `grid`, `free` -- and carries **zero coordinates**. That is the
lane's central claim standing up on its own: a portable layout with no geometry.

## 2. R23.2 -- `grid` is underspecified, so a target must refuse it

Section 5 defines `grid` as *"children in reading order, wrapping; `SPAN` gives
cells consumed."* It never says **where it wraps.** A grid needs a column count and
the table has nowhere to put one.

Section 5 also says an absent dimension is never defaulted to a number, and R12.3
says a target that derives one must record it and must never write it back. Those
two rules together forbid the obvious shortcut of assuming two columns because
`STUDENTS.SCX` and `ACCOUNTS.SCX` happen to be two.

So: **a `grid` container states its column count in a `Columns` property, and a
container with `FLOW = grid` and no `Columns` is refused and named.** Measured, on
a document authored to contain one of each:

```
REFUSED grid on G2 -- FLOW=grid with no Columns property;
                      section 5 does not say where it wraps
```

This is the third time this lane has landed on the same rule from a different
direction. R7: an unbound control must not render as an ordinary empty box. R22.4:
an item whose capability is absent must not render as an ordinary live item. R23.2:
a container whose layout is unspecified must not render as an ordinary stack.

## 3. R23.3 -- `free` with no `ORIGIN` must say it derived

`free` means positioned by `ORIGIN`, and a `free` container whose children have no
`ORIGIN` leaves only `ORDINAL`. Using it is reasonable; using it silently is not:

```
DERIVED position for L9 -- FLOW=free with no ORIGIN; fell back to ORDINAL order
```

## 4. R23.4 -- the inference was being asked about containers that have no layout

R19 measured 228 container groups in the corpus and reported 16% expressible as
`row`, `column` or `grid`. Reproduced exactly: **228 groups, 36 expressible,
15.8%.**

But 14 of those 228 parents are `dataenvironment`, `cursor` or `relation`. A
DataEnvironment is not a layout group -- its children are cursors, they all sit at
top 0, and a coordinate heuristic asked about them answers `row`. **Nine of the 21
`row` classifications are DataEnvironments.**

`import_scx.py` has always skipped them; `SKIP = {'dataenvironment','cursor',
'relation'}` turns them into `SOURCE`, not objects. So the design table was never
polluted -- **the measurement was.** `infer_flow.py` now imports the importer's own
`SKIP` rather than keeping a second opinion about what a visual object is.

| | groups | `free` | `row` | `column` | `grid` | expressible |
| --- | --- | --- | --- | --- | --- | --- |
| all parents (R19) | 228 | 192 | 21 | 3 | 12 | 36 (15.8%) |
| **visual parents only** | **214** | **188** | **11** | **3** | **12** | **26 (12.1%)** |

R19's direction is **strengthened**, not overturned: `free` rises from 84% to
87.9%. Its headline number was off by 3.7 points, and its `row` count was inflated
by 91%.

The general lesson is the one R22.1 arrived at from the other side. R19 measured
carefully and got a number that was wrong because of what it counted, not how it
counted. A population needs a definition, and here the definition already existed
in a neighbouring file.

## 5. What this changes

- `PROPS` gains `Columns` on `grid` containers. This is a property, not a column --
  the schema is still unchanged since gate 10.
- `uidef_tk.py` reads `FLOW` from the container and implements all four values.
- `infer_flow.py` measures visual containers only.
- R19's corpus figures are superseded by the table in section 4. R19's *ruling*
  stands; its arithmetic is corrected here rather than edited there.

## 6. Housekeeping found on the way

Four committed tools carried `sys.path.insert(0, '/tmp/gen')` -- the authoring
container's scratch directory, hardcoded into shipped code: `author_uidef.py`,
`dispatch_test.py`, `infer_flow.py`, `uidef_tk_menu.py`. They ran on the
maintainer's machine only because Python also puts the script's own directory on
the path, so the dead entry was harmless by luck. All four now resolve relative to
`__file__`, which is what the other six already did.

## 7. Still open

- **`FLOW` on non-containers is not validated.** `import_mnx.py` writes
  `FLOW = column` on every menu item, and a plain item is not a container. It is
  harmless today because the menu renderer ignores `FLOW` -- which is exactly the
  condition that let R23.1 survive unnoticed. `uidef.validate()` cannot check this
  yet: a menu container is marked by `Container = .T.` in `PROPS` rather than by
  `KIND`, so the validator has no reliable container test. Either menu containers
  get their own `KIND`, or the validator learns the `PROPS` flag. Owner decision.
- **`SPAN` is exercised in one direction only.** The authored grid spans two
  columns. Row spanning is neither implemented nor forbidden, and section 5's
  "cells consumed" does not distinguish them.
- **`row` and `column` are still unrendered against real imports.** The 11 `row`
  and 3 `column` groups are all in third-party corpus forms, which stay outside the
  repo with their licence undetermined. The authored document proves the consumer;
  it does not prove those specific documents.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Explicit paths only; no `git add -A`. Review before staging -- the author does not
self-approve.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_FLOW_CONTAINER_RULING_V1.md
git add docs/maintenance/evidence/AIF120_flow_render.txt
git add docs/maintenance/evidence/AIF120_flow_ab.png
git add gui/uidef/uidef_tk.py
git add gui/uidef/author_flow.py
git add gui/uidef/infer_flow.py
git add gui/uidef/author_uidef.py
git add gui/uidef/dispatch_test.py
git add gui/uidef/uidef_tk_menu.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R23 -- FLOW belongs to the container; grid must state Columns; R19 corpus figures corrected"
```
