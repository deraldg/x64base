---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-014
  recorded_at_utc: 2026-08-19T00:38:36Z
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
    baseline_commit: c21413a36
  authorization:
    requested_by: maintainer (member.derald), in-session, "good progress, keep going";
      granted the agent access to C:\Users\deral\OneDrive\Documents\Visual FoxPro Projects
      after the VFP 9 install proved to have no FILESPEC directory.
    scope: >
      First .VCX measurement in this lane. Records how .VCX encodes scale mode,
      independently corroborates R13's RESERVED2 mechanism, extends the base-class
      vocabulary, and corrects a claim this run nearly made about menu evidence.
  report:
    path: docs/maintenance/AIF120_VCX_SPECIMEN_V1.md
    kind: measurement
---

# AIF-120 -- the first `.VCX`, and what it says about R2 and R13

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Source: `C:\Users\deral\OneDrive\Documents\Visual FoxPro Projects\LIBS\`.
Fixture: `tools/vfp/fixtures/TEST_APP.VCX` / `.VCT`, byte-identical copies.

The lane went looking for `FILESPEC\90SCX.dbf`, Microsoft's own specification
table. **VFP 9 has no `FILESPEC` directory** -- Microsoft's page lists it for
VFP 8 and earlier, so it appears not to ship in 9. The project directory turned
out to hold something else worth having.

## 1. `.VCX` encodes scale mode as a WORD, in a column

`test_app.vcx`, 29 records, 23 columns, width arithmetic checks.

**`RESERVED6 = "Pixels"`** on 14 of 29 records -- every class definition. Not a
number, not in `PROPERTIES`, a literal word in a reserved column.

Set against what this lane already measured for `.SCX`:

| format | where scale mode lives | how it is encoded |
| --- | --- | --- |
| `.SCX` | the `PROPERTIES` memo of the form record | `ScaleMode = 3` -- a numeric VFP enum |
| `.VCX` | the `RESERVED6` column of each class record | `Pixels` -- a word |

**Two sibling formats, one concept, two encodings, in different places.** R2
ruled that the DSL must carry an explicit scale mode and that a reader must
record which default it applied. That ruling is unchanged and better supported.
What is new is for **R10**: the formats differ not only in how they parent
records, but in *where and in what vocabulary they encode the same property*. An
importer keyed on "look in `PROPERTIES` for `ScaleMode`" reads `.SCX` correctly
and silently finds nothing in `.VCX` -- the failure R2 exists to prevent,
arriving through a different door.

For gate 10: the design table needs one scale-mode field with one encoding, and
the import layer needs a per-format rule for locating it. That is a mapping
concern, not a schema concern, and the schema should not inherit either spelling.

## 2. R13's mechanism corroborated from a second format

R13 rests on `RESERVED2` being a per-definition record count -- inferred from
KB Q145742 and from three `.SCX` files, then confirmed when supplying it made
VFP open our generated form.

The `.VCX` says it independently. Every one of the 14 class definitions carries
`RESERVED2 = 1`, and every one is a single record with no members. **Count of
records in the definition = 1.** Our `.SCX` DataEnvironment carried `2` and had
exactly one member. The rule holds across both formats and both arities.

`RESERVED1` is confirmed as overloaded, exactly as KB Q145742 describes:
`VERSION =   3.00` on the header record, and the literal `Class` as the marker on
each class-definition row.

**`RESERVED4` remains unexplained.** Empty in all 29 `.VCX` records; VFP wrote
`1` into it on our `.SCX` DataEnvironment when it saved. Two formats, no
explanation. Recorded as open rather than guessed.

Also measured and empty: `RESERVED7` (documented as class descriptions) and
`RESERVED8` (documented as `#INCLUDE` / `NOINIT`), 0 of 29 each. Absence is a
measurement here, not a silence -- this library declares no descriptions.

## 3. Vocabulary: 24 base classes becomes 26

New in `.VCX` and never seen in any `.SCX` specimen: **`toolbar`** (x2) and
**`custom`** (x1), alongside `form` (x10) and `container` (x1).

`custom` matters more than its count. It is the non-visual base class, and a
lane whose stopping rule is "no construct may expose the target's object model"
now has a measured example of a class that has no visual representation at all.
Whether the DSL admits non-visual classes is a gate 10 question this specimen
raises and does not answer.

`METHODS` and `OBJCODE` are empty in all 29 records, so this library is a
framework skeleton -- 14 class stubs, no behaviour. R4's scope boundary is
untouched by it.

## 4. A claim this run nearly made, and the measurement that stopped it

The `MENUS` folder holds eight `.MNX` files where the lane had four: `mcc_go`,
`mcc_main`, `mcc_top`, `mcc_append` beside the known `test_*` set. Record counts
line up exactly -- 14, 78, 78, 35 -- and the working note drafted at that moment
said the menu evidence had **doubled to 410 records**.

`cmp` says all four `mcc_*.mnx` are **byte-identical** to their `test_*`
counterparts. There are still 205 menu records, held twice.

M3's zero-geometry finding is unchanged and was never at risk. What was at risk
was a count in a document, and the house rule it would have broken is the one
about counting successes rather than attempts: **two copies of a file are one
specimen.** The `.VCT` memo sidecars do differ (23,349 vs 9,784 bytes) and the
two `.VCX` differ slightly, so the class libraries are genuinely two artifacts;
the menus are not.

## 5. What is still missing -- with one retraction the maintainer caught first

The project's `FORMS`, `GRAPHICS`, `REPORTS`, `DATA`, `INCLUDE` and `HELP`
folders are all **empty** on disk (two directory entries each, `.` and `..`).
They are visible in Explorer with OneDrive sync badges, so the content is
plausibly cloud-resident and not materialised locally.

> **CORRECTED IMMEDIATELY, by the maintainer, before this document was committed.**
> The sentence originally here -- "no specimen so far contains an `image`,
> `shape`, `line` or `grid`" -- is **false**, and it is false about a file this
> lane has held since day one. `form1.scx` carries **24 distinct base classes in
> a single 32-record file**, including `image`, `shape`, `line`, `grid` (x2),
> `pageframe`, `optiongroup`, `commandgroup`, `combobox`, `listbox`, `spinner`,
> `timer`, `hyperlink`, `olecontrol` and `oleboundcontrol`. It is a deliberate
> vocabulary sampler, and the charter already says so in the amendment that
> introduced R5-R7.
>
> Measured now rather than recalled:
>
> | specimen | records | distinct base classes |
> | --- | --- | --- |
> | `form1.scx` | 32 | **24** |
> | `ACCOUNTS.SCX` | 26 | 8 |
> | `STUDENTS.SCX` | 24 | 6 |
> | union | | 24 -- all of them from `form1.scx` |
>
> **So the graphics vocabulary is not missing and never was.** R6's implicit
> children were derived from this file's `ColumnCount`, and R7's OLE ruling from
> its 2,560-byte OLE2 payload. Nothing in `GRAPHICS` is needed for either.
>
> This is the fourth instance in this lane, in one session, of asserting absence
> without measuring -- and the worst of the four, because the fact was already
> written in the lane's own charter, which this run read. The other three at
> least required a search to have missed something. This one required ignoring a
> sentence.

What the lane still lacks is narrower than the retracted sentence implied: a
**hand-authored `.SCX` carrying real method code** (R4's remaining item, all
three form specimens being designer output), and any `.FRX` at all -- the report
format is named in the charter's interchange table and has never been opened.
If the `REPORTS` folder can be made local, that is the gap worth filling.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_VCX_SPECIMEN_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add tools/vfp/fixtures/TEST_APP.VCX tools/vfp/fixtures/TEST_APP.VCT
git status --short -uall
git commit -m "AIF-120: first .VCX specimen -- scale mode as a word in RESERVED6; RESERVED2 corroborated; vocabulary 24 -> 26"
```
