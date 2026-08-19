---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-031
  recorded_at_utc: 2026-08-19T10:10:00Z
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
    baseline_commit: 52831534b
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just woke up an hour ago ---
      go go go!" -- taking R22's open item, the per-document capability manifest.
  report:
    path: docs/maintenance/AIF120_MANIFEST_AND_FONTREF_V1.md
    kind: ruling
---

# AIF-120 -- R24: ask the table, not the window; and a reference is not a measurement

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R22 left this open:

> The refusal report is per-render, not per-document. A target cannot ask "will
> this menu work here?" without building it.

`tools/uidef/manifest.py` answers it. Running it over the lane's six documents
found two defects in fields the lane has been writing for a week and nothing has
ever read.

## 1. R24.1 -- a document's requirements are computable from the table alone

By this point the lane had three refusals that only appear while building a
window: R7 (a control bound to nothing), R22.4 (an item whose capability the host
lacks), R23.2 (a container whose layout is unspecified). All three are knowable
from the table.

A **manifest** is what the document requires: kinds, `FLOW` values, `DISPATCH`
values, host capabilities, `SPAN`, `FONTREF` validity, whether it needs `ORIGIN`,
how many controls are bound. A **profile** is what a target provides. The
difference is the refusal list, and it needs no toolkit -- only the tk *profile*
imports tkinter, and the analysis runs anywhere. Verified on the maintainer's
machine, which has no tkinter at all.

Outcomes are graded, because "will it work" is not a yes or no:

| | meaning |
| --- | --- |
| `REFUSE` | the target cannot render this; the document is out of its reach |
| `DEGRADE` | it renders, less well -- `ORIGIN` ignored, for instance |
| `DERIVE` | the target must invent something and must say so (R12.3) |
| `REQUIRE` | the target must supply something the table cannot -- a data source |
| `NOTE` | worth knowing, refuses nothing |

**The static answer agrees with the runtime one.** The manifest says
`REFUSE grid container G2` and `REFUSE FONTREF 9`; the renderer, given the same
documents, prints `REFUSED grid on G2` and `FONTREF 9 on L5 names no usable FONT
row`. That agreement is the claim being tested here, and it holds on every
document in `docs/maintenance/evidence/AIF120_manifest.txt`.

Profiles are **imported from the targets**, never restated. `uidef_tk.py` now
exposes `KINDS_RENDERED`, `FLOWS_SUPPORTED` and `DISPATCH_SUPPORTED`, and
`uidef_tk_host.py` exposes `CAPABILITIES`; both assert at run time that the
constant still matches the implementation. R22.1 and R23.4 were both caused by two
files holding an opinion about the same fact.

## 2. R24.2 -- `FONTREF` must resolve the object's own font

`import_scx.py` set `FONTREF` like this:

```python
'FONTREF': 1 if fonts else 0,
```

Every object in every imported document pointed at font table entry **1**. The
measurements that follow are all from the corpus, on the maintainer's machine.

**1,688 of 3,010 objects (56%) declare their own `FontName`**, across 151 of the
170 files. All of that was discarded.

And the font table is real, not decorative. An object's `FontName` plus `FontSize`
resolves to a line of its own file's metrics cache in **1,670 of 1,688 cases --
98.9%**. The RESERVED record's lines are the document's font table, and an object
indexes into it. That is measured, not assumed.

So `FONTREF` now resolves the object's declaration. Re-importing the corpus:

| | before | after |
| --- | --- | --- |
| objects selecting their own font | 0 | **1,540 of 2,186 (70.4%)** |
| objects taking the target default | 2,186 | 646 (29.6%) |
| FONT rows added for a declaration the cache lacked | -- | 16 |

The 1.1% that do not resolve are a cache that lagged an edit -- `custorder.scx`
declares Comic Sans MS 18 where its cache holds 12 and 10. Those get a FONT row
built from the declaration and marked `PROVENANCE = derived`. **A cache is allowed
to be stale; the object's own declaration is the truth**, and snapping it to the
nearest cache line would launder a guess into a measurement, which R12.3 already
forbids for dimensions.

An object that declares nothing gets `FONTREF = 0`, the target default the field
table already defines -- not 1. All three in-repo `.SCX` fixtures declare no font
anywhere, which is exactly why 20 objects sat pointing at Arial 9 by assertion and
nobody saw it.

`docs/maintenance/evidence/AIF120_fontref.png` is the consumer half: three labels
in three fonts selected by index, one at `FONTREF = 0` in the target default, and
one at `FONTREF = 9` refused by name.

## 3. R24.3 -- `pageset` was in the vocabulary and in no consumer

The manifest's first run over `form1.scx` printed:

```
REFUSE   kind pageset (x1)   target does not render this kind -- contract s4
```

`pageset` is in the contract's KIND table, and `import_scx.py` has always mapped
VFP's `pageframe` onto it. `uidef_tk.py` simply had no factory for it, so the
reference consumer refused every tabbed form it was ever handed. A `ttk.Notebook`
was four lines away. `docs/maintenance/evidence/AIF120_pageset.png` is two tabs,
one of them a `FLOW = column` page and the other a `FLOW = row` page.

## 4. The pattern these three share

R23.1 was a field the contract put on containers and the consumer read off
children. R24.2 is a field the importer wrote and no consumer read. R24.3 is a kind
the importer produced and no consumer rendered.

**Every one of them survived because production and consumption were never checked
against each other.** A round trip is not a test if only one end is implemented.
The manifest is the cheap version of that check -- it compares what documents
require against what targets declare, without either side having to run.

## 5. A false defect I nearly reported

The first version of the manifest checked `FONTREF` against the `OBJID` of the
FONT rows and reported *"no FONT row with that OBJID"* on every imported form in
the lane. That is not what the field says. The contract's field table:

> `FONTREF` | N(3,0) | O | 1-based index into this document's `FONT` rows. 0 =
> target default

An index, not a name. I wrote a drift check that was itself drift, by assuming
reference semantics instead of reading the field table -- the same mistake R22.1
warns about, made inside the tool built to catch it. Reading the contract before
writing the finding is what caught it, and it is the only reason the real defect
below it was found rather than buried under a false one.

## 6. What this changes

- **No schema change.** Sixth ruling running. `FONTREF`, `KIND` and the FONT rows
  all already existed; they were being produced and not consumed.
- `import_scx.py` resolves per-object fonts and marks derived FONT rows.
- `uidef_tk.py` applies `FONTREF`, renders `pageset`, and exposes its vocabulary.
- `uidef_tk_host.py` exposes its capability vocabulary.
- `tools/uidef/manifest.py` is new, with `author_fonts.py` and `author_tabs.py`.

## 7. Still open

- **The profile is hand-written for a target that is not the reference.** The
  `minimal` profile in `manifest.py` describes a target nobody has built. It
  exercises the checker, and it proves nothing about a real second backend.
- **FONT metrics beyond name and size are undecoded.** A cache line is
  `Arial, 0, 9, 5, 15, 12, 32, 3, 0`. Field 1 is the name and field 3 the point
  size -- measured, 98.9% resolution. The other six are carried verbatim as
  `Metrics` and no claim is made about them. R17's width regression came from
  measuring rendered text, not from reading these.
- **271 FONT rows are carried and unreferenced** after the corpus re-import. Some
  are metrics for objects whose kinds v1 refuses; the rest are unexplained.
- **The manifest does not check `BINDING` against a schema.** It reports that a
  document needs a data source; it cannot say whether a given one satisfies it.
  R17 says a bound control's width lives in the schema, so this is the natural
  next join.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Explicit paths only; no `git add -A`. Review before staging -- the author does not
self-approve.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_MANIFEST_AND_FONTREF_V1.md
git add docs/maintenance/evidence/AIF120_manifest.txt
git add docs/maintenance/evidence/AIF120_fontref.png
git add docs/maintenance/evidence/AIF120_pageset.png
git add tools/uidef/manifest.py
git add tools/uidef/author_fonts.py
git add tools/uidef/author_tabs.py
git add tools/uidef/import_scx.py
git add tools/uidef/uidef_tk.py
git add tools/uidef/uidef_tk_host.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R24 -- a document manifest answers refusal from the table; FONTREF resolves the object's own font; pageset renders"
```
