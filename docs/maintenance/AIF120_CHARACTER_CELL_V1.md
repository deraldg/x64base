---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-043
  recorded_at_utc: 2026-08-19T12:30:00Z
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
    baseline_commit: cc91be3da
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- R34
      named a character-cell target as the harshest available test and nothing had
      run it.
  report:
    path: docs/maintenance/AIF120_CHARACTER_CELL_V1.md
    kind: ruling
---

# AIF-120 -- R35: a target with no pixels and no fonts, and what had to degrade

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Tk and HTML are both retained-mode widget toolkits with fonts and pixels. A
character grid has neither, so everything this lane measured in pixels has to
**degrade** rather than translate. `tools/uidef/uidef_text.py`.

## 1. The result first

All five tables render. On `FLOWDEMO` -- a document carrying **zero coordinates** --
the three real backends return **exactly the same verdict from the table alone**:

| target | geometry | verdict on `FLOWDEMO` |
| --- | --- | --- |
| tk | place / pack / grid, pixels | `DERIVE 2, REFUSE 1` |
| html | flexbox / CSS grid, pixels | `DERIVE 2, REFUSE 1` |
| **text** | **character cells, no fonts** | **`DERIVE 2, REFUSE 1`** |

Three unrelated layout models, one answer. That is the strongest statement
available for section 5's claim that `FLOW` is the portable geometry.

## 2. R35.1 -- a coarse target must BAND before it quantises

This is the finding worth the exercise.

`ORIGIN` is in pixels; a cell is roughly 7 px by 20 px. Converting each control's
`ORIGIN_TOP` independently put `Sid:` on one character row and its own field on the
next, and did the same to `Major:`. **A label sits a few pixels off its own field's
baseline**, and integer division turns that into a different row.

That is R19's finding exactly, and R19 was about **inference**. It governs
**rendering** too, and nothing had noticed:

```
BANDED 19 ORIGIN_TOP values into 10 visual rows on O001 within 8 px --
quantising each one alone splits a row in two (R19, R35.1)
```

> **R35.1.** A target whose unit is coarser than the source's must band
> coordinates into visual rows before quantising them. Quantising each value
> independently splits a row a human sees as one.

Nineteen values, ten rows, on a form that has nine label-and-field pairs plus a
panel. The banding tolerance is 8 px and it is derived, so it is declared.

## 3. R35.2 -- R17 and R25 stop being regressions and become identities

R17 fitted a bound control's width to its field, R25 corrected that to its mask,
both in pixels with a slope and an intercept measured on one machine.

On a character grid there is no slope and no intercept. **The width is the mask
length.** `Gender` is `C(1)` with mask `X` and renders `[_]`; `Email` is `C(40)`
and renders forty underscores; `Lname` twenty.

A pixel target, a browser sizing in `ch`, and a character grid all size a bound
control from the same variable, with no constants carried between them. That is
what R25 meant by "the mechanism travels and the numbers do not", and this is the
case where the numbers disappear entirely.

## 4. R35.3 -- `ignored` is a conformance outcome the contract cannot express

This target has no fonts. `FONTREF` cannot be honoured and must not be refused --
refusing would throw away a document over a property that does not matter here.

```
IGNORED 3 FONT row(s) and every FONTREF -- this target has no fonts.
```

Section 12 gives a reader three postures: understand every **C** field, tolerate
absent **O** fields, refuse unknown `KIND` loudly. There is no word for *"this is
present, understood, and inapplicable to me"*. `manifest.py` has `REFUSE`,
`DEGRADE`, `DERIVE`, `REQUIRE` and `NOTE`; the contract has none of them.

> **R35.3.** A target may **ignore** an optional property its medium has no concept
> for, and must say so. Ignoring is not refusal and it is not honouring, and
> section 12 should name it.

## 5. R35.4 -- `ORIGIN_SCALE = cell` has never been produced by anything

Measured across the corpus: **20 objects declare a `ScaleMode` and all 20 say
pixels.** Not one document uses foxels. So the `cell` value in section 8's
enumeration has been carried, specified and never exercised -- and gate 11's G-6
already recorded that the section enumerates units and gives conversions for none.

This backend is the first consumer that needs the conversion, and there is no rule
to follow. It divides by 7 and 20, chosen from R25's own measurements, and reports
the choice as derived on every render.

> **R35.4.** Either section 8 gives conversions between its units, or it should
> enumerate only `px`. An unconvertible unit is a promise the format cannot keep.

## 6. Two defects in my own backend, both already ruled on elsewhere

Recorded because of what they repeat:

- **Containers were sized by their title before their content was measured**, so
  every box clipped what was inside it. That is **R30.3** arriving on a third
  target: a container's size comes from its children unless something else supplies
  it.
- **Containers were laid out sequentially while controls were positioned
  absolutely**, inside the same `free` parent -- so the empty button panel landed on
  top of the first two rows of the form. Mixing two strategies in one parent is not
  a rule anyone wrote down, and perhaps should be.

## 7. Still open

- **wx remains the important one.** All three backends are Python and none exercises
  `DISPATCH = worker` or the R21/R26 threading rules. This target declares `ui`
  only, which is honest and also means the whole dispatch model is still tested on
  Tk alone.
- **No menu rendering.** `KIND = menu` is refused by both the HTML and text targets.
- **The banding tolerance is a guess.** 8 px works on these documents; nothing
  measures what it should be, and R19 used 6 for inference and this uses 8 for
  rendering without a reason for the difference.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_CHARACTER_CELL_V1.md
git add docs/maintenance/evidence/AIF120_text.txt
git add tools/uidef/uidef_text.py
git add tools/uidef/manifest.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R35 -- a character-cell backend; band before quantising, and ORIGIN_SCALE=cell has never been produced by anything"
```
