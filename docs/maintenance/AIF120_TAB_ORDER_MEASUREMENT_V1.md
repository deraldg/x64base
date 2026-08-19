---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-033
  recorded_at_utc: 2026-08-19T10:40:00Z
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
    baseline_commit: 8047be25b
  authorization:
    requested_by: maintainer (member.derald), in-session. R25 raised `tabindex` as an
      owner decision; this measures it so the decision is cheap. It deliberately rules
      nothing.
  report:
    path: docs/maintenance/AIF120_TAB_ORDER_MEASUREMENT_V1.md
    kind: measurement
---

# AIF-120 -- is tab order derivable? A measurement, not a ruling

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R25 section 8 raised `tabindex` and left it to the owner. `ORDINAL` is *layout*
order; tab order is a second, independent order over the same children, and the
design table has nowhere to put it. **This document rules nothing.** It answers the
one question that makes the decision cheap: can a target derive tab order, or must
the table carry it?

## 1. The population

Every `.SCX` in `D:\dev\vfp-corpus`, every container group with three or more
children that declare a `TabIndex`: **171 groups, 1,689 tab stops.**

## 2. Does tab order equal an order the table already has?

| candidate order | exact match |
| --- | --- |
| document order (what `ORDINAL` currently is) | 9 of 171 (**5.3%**) |
| reading order -- top band, then left | 44 of 171 (**25.7%**) |
| column-major -- left, then top band | 19 of 171 (**11.1%**) |
| **any of the three** | 52 of 171 (**30.4%**) |
| **none of the three** | 119 of 171 (**69.6%**) |

The reading order above bands the `TOP` values within 8 units before sorting. That
matters: my first pass sorted on raw `TOP` and scored 15.8%, because a label sits a
few units off its own field's baseline and raw sorting splits one visual row in
two. **That is R19's finding and 5b's mistake, made again here by me, five hours
after ruling on it.** Banding it recovers ten points.

## 3. How wrong is derived tab order?

Not the same question, and the more useful one:

| measure | value |
| --- | --- |
| normalised inversion distance from reading order | **0.141** (0 identical, 1 reversed) |
| groups within a single adjacent swap | 77 of 171 (**45.0%**) |
| stops not in their exact position | 894 of 1,689 (52.9%) |

**Read the 0.141, not the 52.9%.** Positional comparison is inflated by
construction -- one control inserted in the wrong place displaces every stop after
it, so a single error can score a whole group as half wrong. The inversion distance
says the two orders agree on **86% of all pairwise orderings**. I nearly led with
53%, which would have been true and misleading.

So the answer is a shape, not a number: **derived tab order is nearly right and
reliably not exactly right.** A user tabbing through a generated form would mostly
go where they expect, and would hit at least one wrong stop in about seven groups
out of ten.

## 4. What that leaves the owner

Three options the measurement supports. I am not choosing among them.

1. **Carry it.** A named `TabIndex` property in `PROPS`, or a second ordinal beside
   `ORDINAL`. The property is cheaper; the second ordinal is the more honest model,
   because tab order really is an order over the same children and not an attribute
   of one. Cost: one more thing every producer must get right.
2. **Derive it, and say so.** A target computes reading order and declares it
   derived, which is the rule R12.3 and R23.3 already set for a derived position.
   `manifest.py` would report it as `DERIVE`. Cost: about 70% of groups get at least
   one stop wrong, forever, with no way for a document to correct it.
3. **Carry it only where it differs from the derived order.** The measurement kills
   this one: it differs in 69.6% of groups, so the exception is the rule and the
   saving is not worth the branch.

The thing worth weighing: a wrong tab order is not a cosmetic defect in a
data-entry frontend, which is what most of these forms are. It is the failure mode
R7 and R22.4 both describe -- nothing errors, nothing looks broken, and the user
ends up somewhere they did not intend.

## 5. What this does not measure

- **Whether the corpus tab orders are any good.** They are what designers left
  behind; some are certainly accidents of the order controls were dropped on a
  form. "Not derivable" is not the same as "deliberate".
- **`TabStop`.** A control can be skipped entirely. Not counted here.
- **Nested containers.** Tab order crosses container boundaries in real toolkits;
  this measured within one parent only.
- **Menus.** `.MNX` has no tab order at all.

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_TAB_ORDER_MEASUREMENT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: measurement -- tab order is not derivable but is close; inputs for the owner decision R25 raised"
```
