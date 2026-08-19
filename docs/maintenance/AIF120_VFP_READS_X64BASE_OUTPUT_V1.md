---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260818-COWORK-011
  recorded_at_utc: 2026-08-18T15:57:21Z
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
    baseline_commit: 583408cde
  authorization:
    requested_by: maintainer (member.derald), in-session, "The first time I have actually
      used vfp to open a vfp file we made" + screenshot, then "write it up".
    scope: >
      Records the first measurement in this lane running x64base-writes ->
      VFP-reads, and what it does and does not establish. The VFP half was run by
      the maintainer and witnessed by screenshot, not executed by the agent; the
      byte-level half was re-measured in-session. Does not restate R1-R12.
  report:
    path: docs/maintenance/AIF120_VFP_READS_X64BASE_OUTPUT_V1.md
    kind: measurement
---

# AIF-120 -- VFP 9 reads an x64base-written table

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-18.
Baseline `583408cde`. Lane: `application-ui-dsl`.

**Evidence tier: `runtime-proven`, with the witness stated.** Microsoft Visual
FoxPro 9 ran and produced the observed output. It was run by the maintainer on
`grimwood` at 08:52 local, 2026-08-18, and witnessed by the agent as a
screenshot; the agent did not execute it. The byte-level half below WAS executed
in-session against the same file. Both halves are named separately so a later
reader can weigh them separately.

---

## 1. What happened

The maintainer typed, in the VFP 9 Command window:

```foxpro
USE d:\code\ccode\dottalkpp\data\dbf\vfp\students.dbf SHARED
LIST
```

VFP opened it and listed it. Status bar:
`Students (d:\code\ccode\dottalkpp\data\dbf\vfp\students.dbf)  Record: EOF/200
Record Unlocked`.

This is the first time in this lane that the direction ran **x64base writes ->
VFP reads**. Every prior measurement -- the two `.SCX` form specimens, the four
`.MNX` menus, all of R1 through R12 -- runs VFP writes -> we read.

Checked, not assumed: no document in the lane previously claimed this direction.
The only prior "round-trip" in `AIF120_VFP_SCX_EMPIRICAL_BASELINE_V1.md` is
`test_go.mnx` against `TEST_GO.MPR`, which is VFP output against VFP output.

## 2. The file is ours, and the generator is named

Not inferred from the path. The writer is in the tree and tracked:

| what | where |
| --- | --- |
| schema | `dottalkpp/data/scripts/MCC_SCHEMA_CREATE_SANDBOX.dts:92` -- `CREATE FOX26 STUDENTS (SID N(8,0), LNAME C(20), FNAME C(15), DOB D(8), GENDER C(1), MAJOR C(4), ENROLL_D D(8), GPA N(4,2), EMAIL C(40))` |
| writer | `dottalkpp/data/scripts/mcc/mcc_build_vfp.dts:81` -- `USE STUDENTS NOINDEX` then `COPY TO DBF\vfp\STUDENTS AS VFP OVERWRITE` |
| output | `dottalkpp/data/dbf/vfp/STUDENTS.dbf`, 22,385 bytes, sha256 `e0b266a9f4392eb6` |

It is step 8 of 12 in that build. All twelve outputs carry version byte `0x30`
and all twelve are tracked in `HEAD`.

**The bytes VFP read are the bytes in the repository.** File mtime was
2026-07-15 19:30:14 UTC, unchanged after the 08:52 session -- so that session
opened it `SHARED`, read it, and did not write it back. The measurement below is
against that byte stream.

> **AMENDED 2026-08-18T16:21Z, same run.** "VFP did not write it back" is true of
> the 08:52 session and **false of the day**. A later Form Designer session wrote
> exactly one byte -- offset 28, `0x00` -> `0x01`, the header flag declaring a
> production `.CDX` -- and created `STUDENTS.CDX`. All 200 records remain
> byte-identical and the header is otherwise unchanged. This does not weaken
> section 5; it strengthens it, since modifying in place is a harder
> compatibility test than reading. Details and the maintainer decision it needs:
> `docs/maintenance/AIF120_STUDENTS_SCX_SPECIMEN_V1.md` section 2.

## 3. The byte-level half, re-measured in-session

`tools/vfp/read_vfp_binary.py` against the same file:

| property | value | what it means |
| --- | --- | --- |
| version byte | `0x30` | VFP table signature |
| `nrec` | 200 | matches VFP's `EOF/200` |
| `hlen` | **584** | see below |
| `rlen` | 109 | record length |
| width arithmetic | `width_ok: True` | field widths + deletion flag == `rlen` |
| fields | 9 | `SID N`, `LNAME C`, `FNAME C`, `DOB D`, `GENDER C`, `MAJOR C`, `ENROLL_D D`, `GPA N`, `EMAIL C` |
| field types | `C`, `D`, `N` | three of x64base's seven |

**The header is genuinely VFP, not dBASE wearing a version byte.** A plain
header for 9 fields is `32 + 32*9 + 1 = 321`. Measured `hlen` is 584. The
difference is **exactly 263** -- VFP's database-container backlink block. The
writer emits the real structure, not a minimal one that happens to open.

## 4. Field-level agreement with the screenshot

Nine records are legible in the screenshot, `_REC` 192 through 200. Every field
of every one matches what the reader returns: **81 values, no discrepancy.**

| rec | SID | LNAME | FNAME | DOB (screen / stored) | G | MAJOR | ENROLL_D (screen / stored) | GPA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 192 | 50000191 | Robinson | Liam | 09/18/03 / 20030918 | M | BIOL | 11/12/24 / 20241112 | 2.47 |
| 193 | 50000192 | Johnson | Avery | 10/08/01 / 20011008 | F | ARTS | 05/01/24 / 20240501 | 3.19 |
| 194 | 50000193 | Jackson | Mason | 10/04/07 / 20071004 | F | COMM | 04/30/23 / 20230430 | 2.63 |
| 195 | 50000194 | Rodriguez | Liam | 11/06/00 / 20001106 | M | MATH | 10/31/24 / 20241031 | 3.89 |
| 196 | 50000195 | Miller | Parker | 08/24/00 / 20000824 | X | CSCI | 03/30/23 / 20230330 | 3.86 |
| 197 | 50000196 | Perez | Parker | 02/07/01 / 20010207 | F | BIOL | 05/01/23 / 20230501 | 2.69 |
| 198 | 50000197 | Perez | Ava | 02/22/98 / 19980222 | X | ACCT | 05/17/24 / 20240517 | 3.97 |
| 199 | 50000198 | Rodriguez | Evan | 08/18/88 / 19880818 | M | BIOL | 03/07/23 / 20230307 | 3.95 |
| 200 | 50000199 | Davis | Avery | 09/25/89 / 19890925 | M | ACCT | 05/05/25 / 20250505 | 2.11 |

`EMAIL` matches on all nine and is omitted from the table for width; the
screenshot's left-truncated column (`am.robinson91@...`) is
`liam.robinson91@student.mcc.edu`.

## 5. What this establishes -- three claims, each stronger than "it opened"

**C1. The type encoding is correct, not merely the byte count.** A writer that
gets widths right and semantics wrong produces a file that opens and lists
garbage. `DOB D(8)` stored as `20030918` renders as `09/18/03`, and `GPA N(4,2)`
stored as `2.47` renders as `2.47`. Dates and scaled numerics both survive
Microsoft's own field decoder.

**C2. The header flags and lock semantics are acceptable, not just the layout.**
It opened `SHARED` and the status bar reports `Record Unlocked`. A layout-correct
file with wrong header flags fails at open or refuses share mode.

**C3. R10's premise is now demonstrated bidirectionally.** R10 states that across
the designer formats "only the DBF layer is shared." That layer is the load-
bearing assumption under the charter's amendment (b) interchange argument -- a
design table is consumable by other tools *because* it is a DBF. Until today the
evidence ran one way. It now runs both, and the referee is the reference
implementation rather than this project's own test suite.

## 6. What this does NOT establish

Stated explicitly, because the temptation to over-read a first success is exactly
what R1, R2 and R4 each got wrong once in this lane.

- **Nothing about `.SCX` or `.MNX`.** A 9-field data table is the easy case. The
  designer formats add a memo sidecar, 23 columns, and structural conventions
  the DBF layer knows nothing about.
- **Nothing about writing.** VFP read. It did not append, edit, pack or reindex,
  and the mtime confirms it did not write a byte.
- **Nothing about indexes.** The generator runs `USE STUDENTS NOINDEX` and copies
  without sidecars. No `.CDX` was involved.
- **Nothing about the other six field types.** Three of seven appeared. `L`, `M`
  and the rest are untested in this direction.
- **Nothing repeatable yet.** This was one interactive session on one machine.
  It is a demonstration, not a regression test, and it will not notice if a
  future change breaks it.

## 7. The experiment this makes cheap, and worth doing next

Write a minimal `.SCX` with `COPY TO ... AS VFP`, shaped to the 23-column object
schema already measured in `AIF120_VFP_SCX_EMPIRICAL_BASELINE_V1.md`, then
`MODIFY FORM` it in VFP.

If the Form Designer opens a form this project generated, **gate 10's "design
table documented as a standalone contract" becomes checkable against Microsoft's
own tooling instead of against our opinion** -- and the charter's claim that a
generator is "a consumer of a table, not of the parser" acquires its strongest
possible witness. It is also the cheapest available disproof: a designer that
refuses the file names exactly which convention the schema got wrong.

Two things that measurement would need which today's does not: the memo sidecar
(`.SCT`) must be written too, and R6's implicit-children rule means a form with a
grid or pageframe is a harder first attempt than a form with labels and textboxes.
Start with the easy one.

## 8. One widow this document creates, caught before it shipped

`dottalkpp/data/scripts/MCC_SCHEMA_CREATE_SANDBOX.dts` is cited in section 2 as
the schema source and is **not in `HEAD`** (`git ls-tree -r HEAD` -> 0; not
ignored). The writer beside it, `mcc_build_vfp.dts`, is tracked; the schema
script is not. Staged below with this document rather than after it, so this
report is never in a commit that points at nothing.

## 9. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_VFP_READS_X64BASE_OUTPUT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add dottalkpp/data/scripts/MCC_SCHEMA_CREATE_SANDBOX.dts
git status --short -uall
git commit -m "AIF-120: record VFP 9 reading an x64base-written table -- first runtime-proven result in this lane"
```
