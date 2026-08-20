---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-037
  recorded_at_utc: 2026-08-19T11:50:00Z
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
    baseline_commit: b7f292aa6
  authorization:
    requested_by: maintainer (member.derald), in-session. R28.1 named this defect and
      required the importer to say what it drops. This implements that and measures the
      scale, because the scale changes whose decision it is.
  report:
    path: docs/maintenance/AIF120_IMPLIED_CHILDREN_V1.md
    kind: ruling
---

# AIF-120 -- R29: implicit children are not an edge case, they are a quarter of every form

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R6 and section 13 put implicit children out of v1 deliberately, as a bounded
exclusion. The gate 11 implementer found what it costs on one form. This measures
what it costs on all of them, and the number moves it from a scope note to an
owner decision.

## 1. Measured across the corpus

`gui/uidef/import_scx.py` now records every child that exists only as a dotted
property name on its parent -- `cmdadd.caption = "\<Add"` and its kin. Across all
170 `.SCX` files:

| | |
| --- | --- |
| objects actually imported | 2,186 |
| **implied children lost** | **775** |
| files with at least one | 110 of 170 (**65%**) |
| parent objects dropping children | 164 |
| lost per imported object | **0.35** |

**775 of the 2,961 objects a real form contains -- 26% -- never reach the design
table.** Not refused, not counted, not mentioned. Until today, not even logged.

By parent kind:

| parent | children lost |
| --- | --- |
| `form` | 432 |
| `panel` (VFP container) | 203 |
| `group` (command/option group) | 81 |
| `pageset` (pageframe) | **59** |

## 2. R29.1 -- it takes whole categories, not stragglers

The counts hide what is actually gone.

- **59 lost `page` objects.** A `pageset` stores its pages this way. So every
  imported tabbed form is a **pageframe with no pages**. R24.3 taught the renderer
  to draw a `pageset` as a `ttk.Notebook` two hours ago; on `form1.scx` it draws an
  **empty** notebook, and I did not work out why at the time. This is why.
- **81 lost group buttons.** A VFP `commandgroup` or `optiongroup` holds its
  buttons in a `Buttons` collection, which serialises exactly this way. So **every
  imported radio group and command group is empty.**
- **The 10 navigation buttons** the gate 11 implementer found on
  `UIDEF_STUDENTS`'s panel are one instance of the 203.

This is the point R6 could not have known: **dotted properties are not an oddity,
they are how the source format composes controls.** R6 excluded a mechanism while
believing it was excluding an edge case.

> **R29.1.** An object whose children are carried as dotted property names is a
> **composite control**, not a malformed one. A design table that cannot express
> composition cannot represent a quarter of the objects in the documents it is
> derived from.

## 3. R29.2 -- what is implemented, and what is not

**Implemented, per R28.1:** the importer names every dropped child.

```
STUDENTS.SCX -> UIDEF_STUDENTS.DBF  records=24 rlen=169 hlen=808
  IMPLIED CHILDREN dropped -- 2 object(s) name 16 child(ren) only as
  dotted properties (R6 scope, R28.1 naming):
    O001   form      6: label1, layoutsty, shape1, shape2, shape3, shape4
    O020   panel    10: cmdadd, cmddelete, cmdedit, cmdend, cmdexit,
                        cmdfind, cmdnext, cmdprev, cmdprint, cmdtop
```

A loss that is named is a decision the reader can make. A loss that is silent is
the failure R7, R22.4, R23.2 and R28.1 all describe.

**Not implemented:** materialising them. That changes what v1 is, and R6 and
section 13 are the maintainer's scope calls, not the author's. The work itself is
not large -- the dotted keys carry `caption`, `enabled`, `name` and the rest, which
is most of what a `button` row needs -- but geometry is the open question, because
a `commandgroup`'s buttons are positioned by the group, not by coordinates of their
own.

## 4. R29.3 -- two rulings interacting, and what that says

R24.3 fixed a consumer that refused `pageset`. R29 shows the producer had already
thrown away every page. **Fixing the consumer revealed there was nothing to
consume.**

That pairing is worth keeping because it is the third time today the same shape has
appeared, and this instance is the one where both halves were broken at once. A
round trip is not a test if only one end is implemented -- and when both ends are
broken in complementary ways, each end's output looks like the other end's fault.

## 5. What the owner is deciding

Not "should we support an edge case", but:

1. **Materialise them**, and v1 grows a composition rule -- how a composite
   control's children are positioned, whether they get real `OBJID`s, whether they
   round-trip back to dotted properties on export.
2. **Keep excluding them**, now knowing it is 26% of objects and every tab page and
   every radio button, with the loss named at import.
3. **Refuse documents that contain them** -- consistent with section 4's
   refuse-the-whole-document rule, and it would refuse 65% of the corpus.

The measurement does not choose. It does say that option 2 is a different decision
today than it was when R6 was written, because R6 was made without this number.

## 6. Still open

- **Only `.SCX` measured.** `.VCX` class libraries almost certainly compose the
  same way and were not counted. `.MNX` has no composition.
- **The dotted grammar is not fully decoded.** `layoutsty.Shape1.Name` is two
  levels deep; the counting takes the first segment only, so nested composites are
  undercounted, not over.
- **No claim about what the children should look like** if materialised. That is
  the composition rule, and it does not exist yet.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_IMPLIED_CHILDREN_V1.md
git add gui/uidef/import_scx.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R29 -- implied children measured at 775 across the corpus, 26% of all objects; importer now names what it drops"
```
