---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-032
  recorded_at_utc: 2026-08-19T10:25:00Z
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
    baseline_commit: e6205e11c
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just woke up an hour ago ---
      go go go!" -- taking R24's open item, the join between BINDING and a real schema.
  report:
    path: docs/maintenance/AIF120_MASK_WIDTH_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R25: a bound control's width follows its INPUT MASK, not its field

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R24 left the schema join open: the manifest could say a document needs a data
source, not whether a given source satisfies it. `manifest.py --schema` closes
that. Joining the two re-ran R17's regression on new machinery, and R17 turns out
to be right about the direction and wrong about the mechanism.

## 1. R25.1 -- the mask is derived from the schema, exactly

Every bound control in both generated forms carries an `InputMask`, and the mask
is a function of the field:

| field | mask | mask length |
| --- | --- | --- |
| `C(20)` | `XXXXXXXXXXXXXXXXXXXX` | 20 |
| `C(40)` | 40 X's | 40 |
| `N(8,0)` | `99,999,999` | **10** |
| `N(15,2)` | `999,999,999,999.99` | **18** |
| `D(8)` | none | -- |
| `L(1)` | none | -- |
| `M(4)` | none | -- |

Character masks are one `X` per declared character, 8 of 8. Numeric masks are one
`9` per digit **plus the separators the format inserts**, 4 of 4. That is why R17's
correlation against the field was so strong -- the mask is the schema, restated.

## 2. R25.2 -- but the width follows the MASK, and the two differ

`students.sid` is `N(8,0)`. R17 predicts `7.00 x 8 + 11.4 = 67.4 px`. The design
says 72. The mask renders **ten** characters because of the thousands separators,
and ten is what the control is sized for. `accounts.totaldue` is `N(15,2)` and its
mask renders eighteen; R17 predicts 116, the design says 126.

R17 had to absorb that as error. It is not error, it is a different independent
variable.

## 3. R25.3 -- the law

```
width = k * mask_length + 10
    k = 7.00   for X masks     -- EXACT on 6 of 6 at length >= 15
    k = 6.43   for digit masks -- fitted on 4 points, not exact
```

Same intercept for both classes, different slope. That is what a per-character font
advance plus a constant border looks like, and a digit is narrower than an `X` in
the fonts these forms use.

A type with no mask is a constant, not a function of its width:

| type | px | n |
| --- | --- | --- |
| `D` date | **62** | 3 of 3 |
| `L` logical | **18** | 1 of 1 |
| `M` memo | not placed (width 0) | 2 of 2 |

A date is not eight characters of text. It is a formatted field with a fixed
rendered width, and R17's model had no way to say so.

## 4. Measured, 17 bound controls across both forms

| | mean absolute error | max | exact to the pixel |
| --- | --- | --- | --- |
| R17, from the field | **3.4 px** | 10.6 | 0 of 17 |
| R25, from the mask | **1.1 px** | 12.0 | **11 of 17** |
| R25, setting aside two hand-adjusted controls | **0.3 px** | 2.3 | 11 of 15 |

`ACCOUNTS.SCX` alone: **mean 0.1 px, max 0.6, on 8 of 8.**

The two exceptions are both in `STUDENTS.SCX` and both are short masks:
`gender` is `C(1)`, mask `X`, predicted 17, design 20; `major` is `C(4)`, mask
`XXXX`, predicted 38, design **50**. Nothing in the model produces 50 from a
four-character mask, and no minimum width explains both 20 and 50. The most likely
account is that they were widened by hand in the designer. **Named, not
explained** -- an unexplained 12 px on one control is not a reason to add a term.

## 5. R25.4 -- R17 is narrowed, not withdrawn

R17 said: *a bound control's width is in the data schema, not in the design.* The
direction is right and it stands. The mechanism becomes:

> A bound control's width is in its **mask**, and the schema determines the mask.

That matters because the two come apart. A control whose mask is edited away from
its field default -- which the corpus shows happens -- has a width the schema alone
cannot predict.

## 6. R25.5 -- a load-bearing property must be named

The mask was never lost. `import_scx.py` keeps every property it does not
recognise, so it was in `PROPS` all along as `inputmask`, in VFP's own spelling.

R15 set up a shared property language with shared keys; R20.2 said the vocabulary
is the DSL's, not VFP's. Passthrough is right for decoration and wrong for anything
a consumer must understand -- and a consumer that cannot find the mask cannot
reproduce a width this ruling says is derivable. So `InputMask` is renamed to
`Mask` on import.

How big the passthrough surface is, measured over the corpus import:

```
files=170  objects=2186  distinct PROPS keys=649
keys the DSL has named       : 1        (Caption)
keys passing through verbatim: 648
```

**649 property keys, one of them named.** That is not a defect on its own -- most
of the 648 are genuinely decoration, appearing once or twice. But the top of the
list is not: `tabindex` on 1,664 objects, `fontsize` on 1,566, `fontname` on 1,540,
`autosize` on 633. Those are load-bearing by the same argument the mask was.

## 7. What this changes

- `PROPS` gains `Mask`. Still no schema change -- seventh ruling running.
- `manifest.py --schema <dbf>` joins `BINDING` against a real table: unknown alias,
  missing field, type that cannot drive the kind, and the width prediction above.
- R17's model is superseded for prediction. Its ruling stands as narrowed by 5.

## 8. Still open

- **`tabindex` has no name and no field.** 1,664 objects carry it. `ORDINAL` is
  *layout* order; tab order is a second, independent order over the same children,
  and the table has nowhere to put it. It is not a `PROPS` decoration -- a
  generated frontend with the wrong tab order is wrong. Owner decision: a named
  `TabIndex` property, or a second ordinal.
- **`fontname`/`fontsize` are now carried twice** -- resolved into `FONTREF` by R24
  and still passed through verbatim. One of the two should go, and `fontbold` and
  `fontitalic` are in neither the FONT row nor the resolution, so the FONT row is
  the incomplete copy.
- **The digit-mask slope rests on four points.** 6.43 is a fit, not a law, and the
  two forms come from one wizard on one machine with one font. A third form from a
  different source would settle it.
- **Nothing checks that a mask agrees with its field.** The importer now names the
  mask; it does not verify that a `C(20)` field carries twenty X's. The corpus says
  it always did, which is the moment to start checking rather than assume.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Explicit paths only; no `git add -A`. Review before staging -- the author does not
self-approve.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_MASK_WIDTH_RULING_V1.md
git add docs/maintenance/evidence/AIF120_maskwidth.txt
git add gui/uidef/import_scx.py
git add gui/uidef/manifest.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R25 -- a bound control's width follows its INPUT MASK; R17 narrowed; PROPS gains Mask"
```
