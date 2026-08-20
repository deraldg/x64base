---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-020
  recorded_at_utc: 2026-08-19T08:33:59Z
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
    baseline_commit: 44f742102
  authorization:
    requested_by: maintainer (member.derald), in-session, "I think we are fine, continue"
      -- continuing after the provenance question, by producing from the gate 10 contract
      rather than reasoning about it further.
  report:
    path: docs/maintenance/AIF120_UIDEF_FIRST_IMPLEMENTATION_V1.md
    kind: measurement
---

# AIF-120 -- UIDEF exists, and building it found three defects in its own contract

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Gate 10 was drafted hours ago and was tier `planned` -- a specification nobody had
produced from. This is the first production, and it behaved exactly as the rest of
this session has: **reading produced a plausible contract; writing found what was
wrong with it.**

## 1. What now exists

| artifact | what |
| --- | --- |
| `gui/uidef/uidef.py` | the v1 schema, a DBF+memo writer, and a conformance validator implementing contract section 12 |
| `gui/uidef/import_scx.py` | `.SCX` -> UIDEF importer |
| `gui/uidef/generated/UIDEF_STUDENTS.DBF` / `.FPT` | a real UIDEF document, imported from `STUDENTS.SCX` |
| `gui/uidef/generated/UIDEF_FORM1.DBF` / `.FPT` | the same from `form1.scx`, the 24-base-class sampler |

`UIDEF_STUDENTS.DBF`: version `0x30`, 24 records, `rlen` 164, `hlen` 776, width
arithmetic checks, and **`read_vfp_binary.py` reads it** -- the design table is a
DBF this project can already open, which was the whole architectural claim.

`RECKIND` census: 1 `DOC`, 3 `FONT`, 20 `OBJ`. Conformance findings: **none**.

## 2. Defect one -- the validator caught the author violating R5

The first importer keyed object identity on `OBJNAME`. Running it against
`form1.scx` produced:

```text
rec 5: OBJID 'O006' is not unique
rec 6: OBJID 'O006' is not unique
rec 8: OBJID 'O006' is not unique
```

**R5 exists because of that exact file.** It reads: *"Object identity is the
dotted path, never `OBJNAME`. A second specimen (`form1.scx`) carries three
records named `Header1` and four named `Text1`, distinguished only by `PARENT`.
Keying on `OBJNAME` keeps one grid header and drops the rest."*

The ruling was made on this specimen, by this lane, and the importer written after
it committed the error anyway. Fixed by keying on the dotted path; `form1.scx` now
imports with no findings.

**The transferable part is not the bug, it is that the validator caught it.**
Contract section 12's conformance rules were written as prose and implemented as
20 lines of checks; those checks found a ruling violation on the first run. A
specification with an executable validator catches its own author.

## 3. Defect two -- v1's vocabulary refuses 82% of real forms

Contract section 4 says a reader meeting an unknown `KIND` **must refuse the
document and name the kind**, justified by R7: an importer that emits an empty box
produces a document that looks correct and is not.

Measured against 170 corpus forms:

| | |
| --- | --- |
| object records expressible in v1's 14 kinds | **2,186 of 2,751 (79%)** |
| forms importable with **no** refusal | **31 of 170 (18%)** |

So the rule is coherent and the consequence is that **82% of real forms are
refused outright** -- including `form1.scx`, this lane's own vocabulary sampler,
which trips on nine kinds.

**This needs an owner ruling and is not a steward's call.** The tension is real:
refuse-loudly is correct about correctness and useless about adoption. The obvious
middle path is to **refuse the OBJECT, not the DOCUMENT** -- import what is
understood, drop what is not, and record every refusal in the document so nothing
is silent. That is precisely R3's allow-list logic, which the contract already
adopts for *properties*, applied one level up to *kinds*. R7's "refuse loudly"
would then mean loudly in a manifest rather than fatally at the file.

Recorded as a defect against the draft; not patched in.

## 4. Defect three -- and the cheap fix, measured

Which unmapped base classes block the most forms:

| base class | forms blocked | records |
| --- | --- | --- |
| `shape` | 104 | 198 |
| `custom` | 103 | 118 |
| `grid` | 24 | 30 |
| `header` | 18 | 134 |
| `olecontrol` | 15 | 25 |
| `spinner` | 13 | 16 |
| `line` | 8 | 12 |

Cumulative coverage as kinds are added, greediest first:

| add | forms importing clean |
| --- | --- |
| `shape` | 42 of 170 (25%) |
| `+ custom` | **107 of 170 (63%)** |
| `+ grid` | 111 (65%) |
| `+ header` | 122 (72%) |
| `+ olecontrol` | 134 (79%) |
| `+ spinner` | 143 (84%) |
| `+ line` | 150 (88%) |

**Two additions take coverage from 18% to 63%**, and both are defensible against
the stopping rule:

- **`shape`** -- rectangles and lines. Pure decoration, no object model exposed,
  and every platform in the charter's table has one. It was left out of v1 by
  oversight rather than by any ruling.
- **`custom`** -- the non-visual base class. I excluded it in section 4 as
  "non-visual", which was a category error: R14 already rules that handlers are
  references rather than bodies, so a non-visual object that exists to group
  handlers is exactly what the table should carry. A `KIND = object` with no
  geometry and no `FLOW` costs nothing.

The expensive ones stay out for stated reasons: `grid` and `header` need R6's
implicit children, `olecontrol` is R7.

## 5. What section 5b predicted, confirmed by construction

Every imported object landed `FLOW = free` with an `ORIGIN` group, exactly as 5b
said it would. A sample record, read back from the table:

```text
OBJ  O002  parent=O001  ord=1  kind=label
     ORIGIN_TOP = 61
     ORIGIN_LEFT = 10
     ORIGIN_WIDTH = 41
     ORIGIN_SCALE = px
```

The importer infers **nothing** the source does not state -- no derived `FLOW`, no
guessed dimension, `ORIGIN_SCALE` emitted from the source's own `ScaleMode`. That
is R12.3 and section 8 honoured, and it means the contract's advisory `ORIGIN` is
carrying the entire layout of every document this importer produces.

## 6. What is still not done

- **No reader that renders anything.** UIDEF can be written and parsed; nothing
  consumes it to produce a UI. That is gate 11 and it remains the acceptance test
  for the contract.
- **Menus not imported.** `.MNX` -> UIDEF is unwritten; the contract's section 11
  is unexercised.
- **`FLOW` still never exercised.** Every document produced so far is `free`.
  `row`, `column` and `grid` have no producer and no consumer.
- **No round-trip.** UIDEF -> `.SCX` would let VFP judge our output the way it
  judged `X64FORM.SCX`, which was the most informative test of the session.

## 7. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add gui/uidef/uidef.py gui/uidef/import_scx.py
git add docs/maintenance/AIF120_UIDEF_FIRST_IMPLEMENTATION_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: UIDEF first implementation -- writer, importer, validator; three defects found in the gate 10 contract"
```

`tools/vfp/read_vfp_binary.py` is a working copy of the reader and
`gui/uidef/generated/` is output; neither needs tracking.
