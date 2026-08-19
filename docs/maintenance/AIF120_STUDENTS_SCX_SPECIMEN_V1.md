---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260818-COWORK-012
  recorded_at_utc: 2026-08-18T19:25:09Z
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
    baseline_commit: 3a62467fa
  authorization:
    requested_by: maintainer (member.derald), in-session, screenshots of the VFP Form
      Designer holding students.scx built against the x64base-written STUDENTS.dbf.
    scope: >
      Records the third form specimen, what it independently replicates, the one
      correction it forces on R12, and the fact that VFP wrote to a tracked table.
  report:
    path: docs/maintenance/AIF120_STUDENTS_SCX_SPECIMEN_V1.md
    kind: measurement
---

# AIF-120 -- STUDENTS.SCX, the third form specimen

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-18.

The maintainer built a wizard CRUD form in the VFP 9 Form Designer **against
`dottalkpp/data/dbf/vfp/STUDENTS.dbf`** -- the table this project wrote with
`COPY TO ... AS VFP`. Designer title `students.scx`, caption `STUDENTS`, nine
label/textbox pairs bound to the nine fields, a button row, status bar
`Record: 1/200`.

This is **not** the experiment section 7 of `AIF120_VFP_READS_X64BASE_OUTPUT_V1.md`
proposed. That one has this project *writing* an `.SCX` for VFP to open. Here VFP
wrote the `.SCX` and we read it. Worth having anyway, for two reasons below.

## 1. VFP's design tooling accepts an x64base table as a data source

Beyond `USE` and `LIST`: the Form Wizard read the schema, produced a bound
control per field, and the designer navigated the table (`Record: 1/200`). The
`DataEnvironment`/`Cursor` records in the `.SCX` name our file as the source.

## 2. It writes back, and it wrote correctly -- one byte

**`STUDENTS.dbf` is now modified in the working tree.** This amends the claim in
`AIF120_VFP_READS_X64BASE_OUTPUT_V1.md` section 2 that VFP "did not write it
back": true of the 08:52 read-only session, false as of 16:21.

Measured against the committed blob:

| | |
| --- | --- |
| bytes differing | **1** |
| offset | 28 (0-indexed), `0x00` -> `0x01` |
| what that byte is | DBF header flags; bit 0 = production `.CDX` present |
| header otherwise | identical |
| all 200 records | **byte-identical**, 21,801 bytes |
| new sidecar | `STUDENTS.CDX`, 10,752 bytes |

VFP created a production index, set the one header bit that declares it, and
touched nothing else. That is the conservative, spec-correct write, and it is a
stronger compatibility result than the read was: our header was well-formed
enough for Microsoft's engine to *modify in place* rather than refuse or rewrite.

**Maintainer decision needed** -- the modification is uncommitted. Either accept
the flag plus `STUDENTS.CDX`, or `git checkout` the table and delete the `.CDX`.
Accepting changes a tracked fixture that ten `.dts` regression scripts `USE`.

## 3. What it replicates -- four rulings, independently

24 records, 23 columns, width arithmetic checks.

| ruling | prediction | STUDENTS.SCX |
| --- | --- | --- |
| **R1** key on `BASECLASS`, `CLASS` is a theme hint | wizard forms carry both | `embossedlabel`/`label` x9, `embossedfield`/`textbox` x9, `embossedform`/`form`, `txtbtns`/`container`. `CLASSLOC` non-empty in **20 of 24** -- not self-contained. Holds. |
| **R2** explicit scale mode | wizard forms declare one | `Form1 ScaleMode = 3`, and only there. Holds. |
| **R4** `.SCX` import recovers layout and binding, not logic -- a property of *wizard* files | both empty | `METHODS` 0 of 24, `OBJCODE` 0 of 24. Holds. |
| **R12.3** an absent dimension is derived, never defaulted | height omitted on text-bearing controls | 20 of 24 carry geometry and **all 20 are partial**; `label` x9 and `textbox` x9 declare top/left/width with no height; `form` declares height only. Zero font properties. Holds. |

## 4. The correction it forces on R12's M4

R12 measurement M4 reported "**22 of 45** geometry-bearing records declare fewer
than all four values." True, and it buried the real signal by aggregating two
specimens of different kinds. Split three ways:

| specimen | kind | geometry-bearing | partial |
| --- | --- | --- | --- |
| `ACCOUNTS.SCX` | wizard | 22 | **22 (100%)** |
| `form1.scx` | native | 23 | **0 (0%)** |
| `STUDENTS.SCX` | wizard, over an x64base table | 20 | **20 (100%)** |
| combined | | 65 | 42 (65%) |

**Partiality correlates perfectly with wizard-versus-native.** It is a property
of what the Form Wizard emits, not of the `.SCX` format -- which is the identical
mistake R4 was corrected for, arriving one ruling later on a different axis.

Worse, and worth stating plainly: **R12's own disproof condition 4** asked for "a
hand-authored `.SCX` that declares all four dimensions on every control, which
would show M4's partiality as a wizard artifact." `form1.scx` is native, declares
all four on all 23, and was already in the fixture set and already cited by that
same ruling. The disproof material was in hand and the aggregate hid it.

**R12's ruling survives; M4's framing does not.** R12.3 still holds and is if
anything better supported: wizard output is a real and common input, it omits
height systematically, and it carries no font to derive height from -- so the
table must record *unspecified* and let the target compute. What changes is that
R12 must stop implying the format is partial. It is not. Its most common
*generator* is.

## 4b. It also retracts R12's M5 -- the font anchor exists

Found while reading this specimen's raw records to build a writer, then checked
back against both originals.

Every `.SCX` carries two `PLATFORM = COMMENT` records the object-tree pass steps
over: a leading `UNIQUEID = Screen` holding `VERSION =   3.00`, and a **trailing
`UNIQUEID = RESERVED` holding a font metrics table**.

| specimen | reserved-record payload |
| --- | --- |
| `ACCOUNTS.SCX` (wizard) | `Arial, 0, 9, 5, 15, 12, 32, 3, 0` / `Arial, 0, 8, ...` / `MS Sans Serif, 0, 8, ...` |
| `STUDENTS.SCX` (wizard) | identical three rows |
| `form1.scx` (native) | one row, `Arial, 0, 9, 5, 15, 12, 32, 3, 0` |

R12's M5 claimed "zero font properties across all 58 records ... the document
does not carry metrics." **False.** The scan parsed `PROPERTIES` as
`name = value` and counted `font*` keys; the reserved record's payload is
positional CSV with no `=`, so the parser returned nothing and the scan reported
absence. Same trap as M4, same day, one section apart.

The nine positional fields are not decoded here and are not guessed. What is
measured: the table exists in all three specimens, is per-font, and grows with
the number of fonts the form uses.

**It strengthens R12.3.** A target deriving an omitted height can take metrics
the document carries rather than substituting its own font -- more faithful and
more portable than the rule assumed. R12.3's requirement is unchanged; its
derivation now has a named source, and the design table must carry the font
table for a generator to use it.

## 5. What this still does not establish

- Nothing about writing `.SCX` from this project. Section 7 of the runtime note
  remains the untried experiment, and is now better specified: the wizard's own
  output over our own table is the reference to match.
- Nothing about menus, grids, pageframes, or the OLE case (R6, R7).
- The `.CDX` was written by VFP and has not been read by anything here.

## 6. Fixtures added

Copied into `tools/vfp/fixtures/`, verified byte-identical to the originals:

| file | bytes | sha256 (first 16) |
| --- | --- | --- |
| `STUDENTS.SCX` | 3649 | `d7e0e4df48b6c05f` |
| `STUDENTS.SCT` | 7489 | `6caf0899fd045dc0` |

## 7. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
# The specimen, the fixtures, and the two amendments.
git add docs/maintenance/AIF120_STUDENTS_SCX_SPECIMEN_V1.md
git add docs/maintenance/AIF120_COORDINATE_RULING_V1.md
git add docs/maintenance/AIF120_VFP_READS_X64BASE_OUTPUT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add tools/vfp/fixtures/STUDENTS.SCX tools/vfp/fixtures/STUDENTS.SCT
git status --short -uall
git commit -m "AIF-120: STUDENTS.SCX specimen; correct M4 -- geometry partiality is a wizard property, not a format one"
```

```powershell
# SEPARATE, and your call -- the table VFP modified. Inspect before deciding.
git --no-optional-locks diff --stat -- dottalkpp/data/dbf/vfp/STUDENTS.dbf
# accept:
#   $env:X64BASE_ALLOW_DATA = "1"
#   git add dottalkpp/data/dbf/vfp/STUDENTS.dbf dottalkpp/data/dbf/vfp/STUDENTS.CDX
#   git commit -m "AIF-120: accept VFP's production-CDX flag on STUDENTS.dbf"
#   Remove-Item Env:\X64BASE_ALLOW_DATA
# or revert:
#   git checkout -- dottalkpp/data/dbf/vfp/STUDENTS.dbf
#   Remove-Item dottalkpp\data\dbf\vfp\STUDENTS.CDX
```
