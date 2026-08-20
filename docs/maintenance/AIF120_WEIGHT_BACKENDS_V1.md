---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-089
  recorded_at_utc: 2026-08-20T17:00:00Z
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
    requested_by: maintainer (member.derald), in-session -- "continue", taking the
      queue R79 section 7 named: Weight and Fill in the three remaining backends.
    scope: >
      Carry contract 5c into uidef_tk.py, uidef_html.py and uidef_text.py, and
      correct R79's claim about what those backends can do. Writes gui/uidef/ and
      docs/ only.
  report:
    path: docs/maintenance/AIF120_WEIGHT_BACKENDS_V1.md
    kind: ruling
---

# AIF-120 -- R80: `Weight` needs free space, and two of the four backends have none -- which corrects a claim R79 made one ruling ago

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

R79 shipped `Weight` and `Fill` and included a table asserting that all four
backends carry both natively. Carrying the property into the other three found
that table half wrong -- not about the mechanisms, which exist, but about whether
they can do anything. **`Weight` is a share of FREE SPACE, and a container that
sizes to its children has none.** The HTML form was `display:inline-block` and the
character-cell renderer never divides its width; in both, correct CSS and correct
intent would have been emitted and been inert. Fixed where fixable, reported where
not, and R79's claim corrected.

## 1. The correction I owe

R79 section 2 said, of all four backends, "all four carry both, and none needs a
new concept", with this table:

| | along the axis | across it |
|---|---|---|
| wx | `Add(child, proportion, ...)` | `wxEXPAND` |
| Tk | `pack(expand=True)` / `grid(weight=)` | `fill=` / `sticky=` |
| HTML | `flex-grow` | `align-self: stretch` |
| character cell | proportional column share | full span of the cross axis |

Every cell is true about the toolkit and two are false about this lane's backend.
I was reasoning about what a character grid COULD do and what CSS HAS, not
measuring what `uidef_text.py` and `uidef_html.py` DO. Measured:

| backend | container sizing | evidence | `Weight` can mean something? |
|---|---|---|---|
| **wx** | frame sized from `ORIGIN`; sizers divide it | R79's render | **yes** |
| **Tk** | `root.geometry(w x h)` from `ORIGIN` | `uidef_tk.py:319` | **yes** |
| **HTML** | `.form{...display:inline-block}` -- content-sized | `uidef_html.py:317` | **no**, until the form is given a size |
| **character cell** | canvas grows to content; `avail_w` is only ever DECREMENTED, never divided | `uidef_text.py:200,286` | **no**, without a two-pass rewrite |

That is the same error this session has recorded four times in other people's code
and twice in my own: **asserting from the shape of the thing instead of measuring
it.** This time it was in a ruling, one turn old, about the property I was
implementing.

## 2. The rule the correction produces

> **`Weight` is meaningful only in a SPACE-FILLING container.** A container that
> sizes to its children has no free space, so a share of it is undefined. A reader
> whose layout is content-sized MUST report that `Weight` was dropped rather than
> emit an inert property, and MAY become space-filling instead -- but that is a
> change to the reader, not a mapping of the property.

`Fill` is not subject to this. Stretching ACROSS the flow axis is meaningful
whenever the cross axis has any extent at all, which is why HTML's `align-self`
and Tk's `fill=` work in all three.

## 3. HTML -- fixed, because the fix was one honest line

`flex-grow` was emitted into an `inline-block` container: present, correct, inert.
A form that declares `ORIGIN` dimensions now becomes a **sized flex column**, so
its children have something to grow into:

```html
<div class="form sized" style="display:flex;flex-direction:column;...;width:700px;height:400px">
  <select multiple size="4" style="flex-grow:3;flex-basis:0;align-self:stretch"></select>
  <input type="text" style="flex-grow:1;flex-basis:0;align-self:stretch">
```

A `Weight = 0` label in the same document correctly receives neither property.

**A form WITHOUT `ORIGIN` dimensions reports the drop** and stays content-sized --
and measured, that is every fixture in the corpus, including `MAINFRAME`. So the
common case today is the reported one, which is the correct outcome and not a
comfortable one.

## 4. Tk -- implemented, and it loses the RATIO

Tk has a sized window, so there is slack to claim. `expand` is `Weight` and `fill`
is `Fill`, and both now come from the document. Built headlessly and inspected
through the real widget tree, not the source:

```
packed children : 33
claiming expand : 20
claiming fill   : 22
```

**But Tk's `expand` is a BOOLEAN.** It divides slack equally among everyone who
claims it; it has no ratio. So `Weight = 3` against `Weight = 1` becomes "both
expand", and the intent survives while the proportion does not. The generator
reports it:

```
DEGRADED Weight=3 on NB -- Tk pack expand is a boolean and divides slack
EQUALLY; the ratio is lost (R80)
```

`grid()` has a real per-row/column `weight`, so a future Tk backend that packs
through `grid` rather than `pack` could carry the ratio. Named, not done -- it is a
layout-strategy change to that backend, and R79's rule about reporting half-honoured
properties is what makes deferring it honest.

## 5. Character cell -- reported, and the rewrite named

`draw()` measures each child and grows the canvas; `avail_w` is passed down as
`avail_w - 2` and never divided. Making `Weight` work means making the renderer
space-filling: a two-pass measure-then-distribute `draw()`. That is a real change
to the oldest backend in the lane and it is not this ruling's business. Today:

```
DROPPED Weight on 2 child(ren) of MAIN -- this target is content-sized and
has no free space to divide (R80)
```

Five such notices on `MAINFRAME`, one per flowed container carrying weights.

## 6. Proof

| | |
|---|---|
| wx | unchanged; **18/18 fixtures still byte-identical** |
| HTML, sized form | `flex-grow:3` / `flex-grow:1` / `align-self:stretch` emitted, `Weight = 0` gets nothing |
| HTML, unsized form | drop reported; measured, that is every fixture in the corpus |
| Tk | real widget tree inspected under Xvfb: 20 children claiming `expand`, 22 claiming `fill`, of 33 packed |
| Tk ratio | `DEGRADED` reported for every `Weight > 1` |
| character cell | `DROPPED` reported per container; five on `MAINFRAME` |

Every one of the three new behaviours is a REPORT rather than a silent success or a
silent failure, which is the only reason a half-supported property is safe to ship.

## 7. Open

- **Character-cell two-pass `draw()`** -- section 5.
- **Tk through `grid()` rather than `pack()`** to carry the ratio -- section 4.
- **`FLOW = grid` row/column growth** -- unchanged from R79.
- **R77's negotiable geometry** -- unchanged.
- **MSVC** -- unchanged, and now the oldest open item in the lane by several rulings.

## 8. Good Neighbor

| | |
|---|---|
| What changed | `gui/uidef/uidef_html.py`, `uidef_tk.py`, `uidef_text.py`; this ruling; ledger rows. `uidef_wx.py` and `manifest.py` untouched |
| Whose area | AIF-120. `src/` untouched |
| Authorization | maintainer, in-session: "continue" |
| How to verify | `python uidef_text.py MAINFRAME.DBF` for the drops; `python uidef_html.py` on a form with ORIGIN for the flex output; `xvfb-run python3.12` + `pack_info()` for Tk |
| How to undo | `git revert`. wx is byte-identical either way |
| Risk | low. Two backends gained a report, one gained behaviour behind a property that no existing fixture sets |

## 9. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git status -uall

git add gui/uidef/uidef_html.py
git add gui/uidef/uidef_tk.py
git add gui/uidef/uidef_text.py
git add docs/maintenance/AIF120_WEIGHT_BACKENDS_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md

git status -uall

git commit -m "AIF-120: R80 -- Weight needs free space and two backends have none; HTML fixed, Tk implemented and reports the lost ratio, character-cell reports the drop, and R79's backend claim corrected"
```
