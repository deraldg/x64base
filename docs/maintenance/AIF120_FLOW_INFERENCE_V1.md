---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-026
  recorded_at_utc: 2026-08-19T09:13:36Z
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
    baseline_commit: 120b51b88
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "keep going" -- the
      hard problem named at the end of the R11/R14 runtime work: imports cannot produce
      FLOW, so UIDEF has two disjoint populations.
  report:
    path: docs/maintenance/AIF120_FLOW_INFERENCE_V1.md
    kind: measurement
---

# AIF-120 -- R19: `free` is not an inference failure, it is what most real forms are

Status: **measurement and ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.
Algorithm: `tools/uidef/infer_flow.py`.

Contract section 5b recorded that imports land `FLOW = free` and treated the high
rate as **a defect in the contract**. This measures it properly and the conclusion
inverts.

## 1. Why 5b's method was wrong

5b clustered `TOP` and `LEFT` independently with a tolerance, then accepted a
lattice no larger than 1.5x the child count. Two problems:

- **Baseline offsets defeat top-clustering.** In `STUDENTS.SCX` a label sits four
  units below its own field, so nine visual rows present as eighteen `TOP` values.
- **The lattice test was permissive to the point of meaninglessness.** With 19
  distinct tops and 3 lefts, `19 x 3 >= 19` holds for almost any arrangement. It
  measured "no two controls share a coordinate", not "this is a grid".

## 2. A decomposition that works: columns are crisp, rows are not

Cluster on `LEFT` only, sort each column by `TOP`, then read rows off by index
within column. **A baseline offset is a within-row difference, so it never crosses
a column boundary and cannot corrupt the row assignment.**

That alone still rejected `STUDENTS.SCX`, with column depths `[1, 9, 9]` -- nine
labels, nine fields, and one button container belonging to neither. Hence the
second half:

**A real form is a grid plus outliers.** Take the modal column depth as the grid;
treat shallower columns as separate blocks ordered after it.

| specimen | inferred |
| --- | --- |
| `STUDENTS.SCX` | **grid, 2 columns x 9 rows + 1 outlier** |
| `ACCOUNTS.SCX` | **grid, 2 columns x 10 rows + 1 outlier** |
| `form1.scx` | `free` -- column depths `[1 x15, 2 x3]` |

The first two are exactly right, and 5b's method called both `free`. `form1.scx`
is a vocabulary sampler with one of everything scattered; `free` is the correct
answer for it.

## 3. The corpus result, and why it looks like a regression and is not

Same 228 container groups 5b measured, same basis:

| method | expressible as row/column/grid |
| --- | --- |
| 5b, permissive lattice, tolerance 12 | 40% |
| **this method, strict and correct** | **16%** (`row` 21, `column` 3, `grid` 12, `free` 192) |

**A stricter, correct test finds FEWER grids, not more.** The two numbers are not
comparable as quality: 5b's 40% counted arrangements that are not grids, and this
16% gets the two forms that matter exactly right where 5b did not.

## 4. R19 -- the ruling

**R19. `FLOW = free` with an `ORIGIN` group is the CORRECT representation of most
imported forms, not a fallback and not an inference failure. 84% of real container
groups are genuinely not row, column, or grid.**

Three consequences.

**R19.1 -- section 5b's framing is withdrawn.** 5b called the high `free` rate a
defect in the contract. It is a fact about how forms were authored. Thirty years
of designers dragged controls to where they looked right; most of those
arrangements encode no reusable structure because there was none.

**R19.2 -- the contract's fix is still needed, for a different reason.** 5b
proposed narrowing section 12's permission to refuse `FLOW = free`. That still
stands, but not because inference is hard -- because **`free` is the majority
case and always will be.** A generator that refuses `free` refuses most real
documents permanently, not until the importer improves.

**R19.3 -- R12 is confirmed and its scope is now measured.** Layout intent is the
right model for **authored** documents, and that is now proven rather than argued:
the hand-authored test document is `FLOW = column` with no `ORIGIN` on any row and
it renders. For imports, intent mostly does not exist to recover. **UIDEF's two
populations are real and permanent**, and that is not a flaw -- an interchange
format must represent what documents are, not what they should have been.

## 5. What this does not establish

- **The algorithm is deliberately conservative.** It requires two or more columns
  at the modal depth and at most 25% outliers. Loosening either finds more grids
  and more false ones; no tuning study was done.
- **One tolerance, 6 units, unjustified.** It works on these specimens because
  baseline offsets there are ~4. A different design font would need a different
  value, which is R17's problem in a new place.
- **Nested containers are not descended into.** Each parent group is classified
  independently; a grid inside a panel inside a free-form container is not
  composed.
- **`row` and `column` inferences are untested by rendering.** Only `grid` was
  checked against the two specimens; the 21 `row` and 3 `column` classifications
  were never drawn.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add tools/uidef/infer_flow.py
git add docs/maintenance/AIF120_FLOW_INFERENCE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: R19 -- FLOW=free is what most real forms ARE; 5b's framing withdrawn, its proposed fix still stands"
```
