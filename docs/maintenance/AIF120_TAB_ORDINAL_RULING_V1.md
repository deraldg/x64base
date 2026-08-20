---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-035
  recorded_at_utc: 2026-08-19T11:05:00Z
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
    baseline_commit: e5a9c868a
  authorization:
    requested_by: maintainer (member.derald), in-session, one word -- "ordinal" -- in
      answer to the two options in AIF120_TAB_ORDER_MEASUREMENT_V1.md section 4. This
      is the owner's decision implemented, not the author's.
  report:
    path: docs/maintenance/AIF120_TAB_ORDINAL_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R27: tab order is a second ordinal, and the table gains a column

Status: **ruling, review-needed.** Owner: member.derald -- **and this one the owner
decided.** Author: member.ai.claude.cowork, run `COWORK-20260818-001`. 2026-08-19.

`AIF120_TAB_ORDER_MEASUREMENT_V1.md` measured that tab order is not derivable and
offered the owner two ways to carry it: a named `TabIndex` property in `PROPS`, or
a second ordinal beside `ORDINAL`. The owner chose the ordinal.

## 1. This is the first schema change since gate 10

Six rulings in a row changed nothing about the table. This one adds a column, and
that is worth stating rather than slipping in:

```
("ORDINAL",    "N",  5),
("TABORDINAL", "N",  5),      <- new
("SPAN",       "N",  5),
```

Sixteen fields. `rlen` 164 -> **169**, `hlen` 776 -> **808**. Every UIDEF table
written before this commit is at the old length; the reader locates fields by name
from the header, so old tables still read, but nothing produced before today
carries the column.

The reasoning for a column over a property, which is the owner's and not mine:
tab order is an **order over a container's children**, exactly as `ORDINAL` is. It
is not an attribute of the child that happens to be a number. Putting it in `PROPS`
would have modelled it as decoration and let it drift, which is the failure R25.5
had just finished describing.

## 2. R27.1 -- semantics

> **R27.** A container's children carry a second ordinal, `TABORDINAL`, giving
> focus order. It is independent of `ORDINAL`, which gives layout order. `0` or
> absent means the target derives focus order and must declare that it derived it.

- **Requiredness (R13, per direction):** `O` to produce, `O` to consume. A producer
  that knows the focus order states it; one that does not, leaves 0.
- **Derivation:** a target with no `TABORDINAL` derives from reading order and says
  so. Measured, that lands exactly right in 25.7% of groups and within one adjacent
  swap in 45%.
- **`manifest.py` reports it** as a `DERIVE` outcome, and distinguishes the partial
  case -- some children stated, some not -- which is worse than none, because the
  gaps must be interleaved with the declared stops.

## 3. R27.2 -- duplicates are refused to produce and tolerated to consume

`uidef.validate()` now checks that two children of one container do not claim the
same `TABORDINAL`. Across the corpus, after the correction in section 5, **9 files
of 170 contain a genuine within-container duplicate.**

They are real -- `msgbox.scx` has two controls at position 3 and two at 11 inside
one form, and `qbf.scx` has two at 25 in a sequence that otherwise runs 1 to 29.
Refusing them outright would make 5% of real documents unimportable for a defect
that has an obvious resolution, so:

> **R27.2.** A duplicate `TABORDINAL` within a container is refused to **produce**
> and tolerated to **consume**, with `ORDINAL` breaking the tie. A consumer that
> breaks a tie has derived something and says so.

## 4. Populated, measured

Re-importing the corpus with the column:

| | |
| --- | --- |
| objects carrying a `TABORDINAL` | **1,445 of 2,186 (66.1%)** |
| files with a genuine duplicate | 9 of 170 |
| example: `crmfiles.scx` `O002` | `ORDINAL` 1, `TABORDINAL` **5** |

That example is the justification in one row: the same object is first in layout
order and fifth in focus order.

`tabindex` is removed from the `PROPS` passthrough, so it is carried once rather
than twice -- the duplication R25.8 flagged for `fontname`/`fontsize` is not
repeated here.

The three in-repo `.SCX` fixtures declare no `TabIndex` at all, so they import with
`TABORDINAL = 0` throughout and the manifest reports `DERIVE 19 control(s)`. As
with fonts, the generated forms are the unrepresentative case and the corpus is
where the evidence lives.

## 5. A false-positive class I shipped and caught

The duplicate check first reported **116** findings. Reading them rather than
counting them showed that most were in container `''` -- top level. An `.SCX` can
hold a **form set**, several forms in one file, and each form starts its tab
sequence at 1. Comparing them to each other is meaningless.

Excluding top-level objects, which are each their own tab domain, the count falls
to **9**. So 107 of 116 were an artefact of my own grouping key.

Worth recording because of how close it came to shipping as a finding: the number
looked plausible -- 116 across 170 files is the sort of rate this corpus produces
for real defects -- and only the individual rows showed it was wrong. **A count is
not a finding until you have read the rows underneath it.**

## 6. Still open

- **`TabStop`.** A control can be removed from the tab cycle entirely. That is a
  different fact from its position and the table still has no way to say it.
- **Focus order across containers.** Real toolkits tab out of a container into the
  next one. `TABORDINAL` is scoped to one container, and how the sequence composes
  across nesting is not settled.
- **Whether corpus tab orders are any good.** They are what designers left behind.
  Not derivable is not the same as deliberate.
- **`.MNX` has no tab order**, so menus are unaffected.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Run after the R26 commit. The `uidef.py` change alters `rlen`, so anything that
regenerates a UIDEF table should be re-run afterwards.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_TAB_ORDINAL_RULING_V1.md
git add gui/uidef/uidef.py
git add gui/uidef/import_scx.py
git add gui/uidef/manifest.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R27 -- tab order becomes TABORDINAL, a second ordinal column; owner's decision, first schema change since gate 10"
```
