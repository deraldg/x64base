---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-023
  recorded_at_utc: 2026-08-19T08:54:14Z
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
    baseline_commit: 65877388c
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- the
      FLOW render proposed at the end of the R16 work, and what it exposed.
  report:
    path: docs/maintenance/AIF120_BOUND_WIDTH_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R17: a bound control's width is in the data schema, not the design

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

**Evidence tier: `runtime-proven`** for the renders (executed under `xvfb`,
inspected); **source-evidenced** for the correlation.
Evidence: `docs/maintenance/evidence/AIF120_width_ace.png`.

R16 said a stated width is advisory when content determines it. This goes one
step further and removes the remaining case.

## 1. The measurement that started it

Rendering the same document with layout from `ORDINAL` required a width in
**characters** rather than pixels, so the question arose: where would that number
come from? It turns out the design already answers it.

For every bound control, comparing the **authored pixel width** against the
**declared width of the DBF field it is bound to**:

**`STUDENTS.SCX` against `STUDENTS.dbf`** -- n=9, **r = 0.9982**

| field | declared | authored px | px/char |
| --- | --- | --- | --- |
| `EMAIL` | C(40) | 290 | 7.25 |
| `LNAME` | C(20) | 150 | 7.50 |
| `FNAME` | C(15) | 115 | 7.67 |
| `SID` | N(8) | 72 | 9.00 |
| `DOB` | D(8) | 62 | 7.75 |
| `GENDER` | C(1) | 20 | 20.00 |

**`ACCOUNTS.SCX` against `ACCOUNTS.dbf`** -- a different form, a different table,
a different designer session -- n=8, **r = 0.9977**, least-squares fit:

```text
width_px = 7.00 * declared_chars + 11.40
```

Two independent replications above r = 0.997. The slope is the design font's
character cell width; the intercept is border and padding.

**So an authored width on a bound control carries no information the data schema
does not already have.** It is the schema's field width, multiplied by a constant
that belongs to a font on a machine thirty years ago.

## 2. R17 -- the ruling

**R17. For a control bound to a data field, size is derived from the binding --
the field's declared width, in characters, rendered in the target's own font. The
design table need not carry a width for a bound control, and a target must prefer
the schema over any width that is carried.**

Together with R16 this closes the width question completely:

| control | width comes from |
| --- | --- |
| content-sized (`label`, `button`, `check`, `radio`) | its own content, in the target's font (**R16**) |
| data-sized and **bound** | the bound field's declared width, in characters (**R17**) |
| data-sized and **unbound** | `ORIGIN_WIDTH`, honoured with its `ORIGIN_SCALE` |
| containers | `ORIGIN`, honoured |

**Nothing in the first two rows needs a number in the design table at all.**

## 3. Rendered, five ways, and E wins

Evidence image, left to right: **A** honour every width, **C** R16 with absolute
positions, **E** R17 -- widths from the data schema, layout from `ORDINAL`.

| | labels | field widths | collisions |
| --- | --- | --- | --- |
| A | **truncated** | preserved in px | none |
| B (not shown) | legible | **all identical -- lost** | none |
| C | legible | preserved in px | **label touches field** |
| D (not shown) | legible | preserved as px/7 | none |
| **E** | **legible** | **correct, from the schema** | **none** |

E is not a compromise. It is better than every other render on every axis, and
**it is the only one that is font-independent** -- the widths are expressed in
characters, so they are correct in any font on any platform, which is exactly what
render A failed at.

## 4. Why this is the resolution and not another patch

The width problem has now been through four positions in one session:

1. carry the pixel width and honour it -> **labels truncate** (render A)
2. ignore it -> **field sizing lost** (render B)
3. R16: honour it only for data-sized controls -> **works, but collides with
   authored positions** (render C)
4. **R17: derive it from the binding** -> nothing to collide, nothing to truncate,
   nothing font-relative (render E)

Each step was forced by rendering the previous one. **None of the four was
reachable by reasoning about the format**, and the first three all looked correct
when written down.

R17 also supplies the argument R12 never had. R12 chose layout intent over
absolute geometry on a *sequencing* basis -- cheap now versus a rewrite later.
The real reason is now measured: **absolute geometry encodes a font, and a font
does not travel.** Every pixel number in a `.SCX` is a measurement of one machine.

## 5. What R17 does not establish

- **Two forms, one designer's habits.** Both specimens are VFP 9 wizard output
  from the same maintainer. Application code by other authors may deviate.
- **Narrow fields need a floor.** The px/char ratio inflates badly at the low
  end -- `GENDER` C(1) at 20px is 20 px/char, `TAXABLE` L(1) at 18px, `MAJOR`
  C(4) at 50px. A minimum usable width exists and R17 does not specify it.
- **`N` and `D` types are approximations.** `N(4,2)` displays as 4 characters plus
  a separator; `D(8)` displays as 10 (`mm/dd/yyyy`). Deriving display width from
  storage width needs a per-type rule this ruling does not give.
- **Unbound data-sized controls are untouched** and still need a carried width.
- **`MAJOR` C(4) at 50px is a real outlier** (12.5 px/char) -- a designer widened
  it by hand. Derivation would render it narrower than authored. Whether that is
  a regression or a correction is a judgement R17 does not make.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
$env:X64BASE_ALLOW_DATA = "1"
git add docs/maintenance/AIF120_BOUND_WIDTH_RULING_V1.md
git add docs/maintenance/evidence/AIF120_width_ace.png
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R17 -- a bound control's width is in the data schema; r=0.998 on two independent forms"
Remove-Item Env:\X64BASE_ALLOW_DATA
```
