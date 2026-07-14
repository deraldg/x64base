# MCC Sample Data — the Databuild Lane

The My Community College sample dataset, rebuilt reproducibly from one archive.

This is **step 5 of user onboarding**. Everything downstream — HELP files,
lessons, labs, regression canaries — assumes this data exists and is virgin.

```text
1. user downloads the program
2. user reads the instructions
3. user builds the system
4. user builds the runtime
5. user runs the databuild / indexing scripts   <- THIS
```

## The Chain

```text
MyCommunityCollege.zip                    dBase III / MS-DOS. The only original.
        |  extract_mcc_og.ps1
        v
data\dbf\og\                              untouched. Never written to.
        |  mcc_build_x32.dts   COPY AS MSDOS
        v
data\dbf\x32\      + data\indexes\x32\*.cnx
        |  mcc_build_vfp.dts   COPY AS VFP
        v
data\dbf\vfp\      + data\indexes\vfp\*.cnx
        |  mcc_build_x64.dts   COPY AS X64 VECTOR
        v
data\dbf\x64\      + data\indexes\x64\*.cdx      PUBLISHED
                   + data\lmdb\x64\*.cdx.d       DERIVED — never published
```

Each stage derives from the one before it. The archive is the only origin.

## Run It

One command. This is the released entry point:

```powershell
.\dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1
```

It **warns that databases will be created**, shows exactly which existing demo
databases will be **overwritten with fresh copies from the original archive**,
states plainly that any changes to them will be lost, and then **asks before
touching anything**. Nothing happens until you type `YES` — in capitals.

```powershell
.\dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1 -WhatIf   # show the plan, change nothing
.\dottalkpp\scripts\mcc\build_mcc_demo_bases.ps1 -Yes      # skip the prompt (automation only)
```

The prompt lives in PowerShell because DotScript cannot prompt — `BUILDLMDB` is
explicitly *"shell-safe: no nested std::cin prompt reads."* A destructive gate
that the runner would walk straight past is not a gate.

### Doing it by hand

`build_mcc_demo_bases.ps1` runs these for you. Run them yourself if you want to
see each stage:

```powershell
.\dottalkpp\scripts\mcc\reset_mcc_fixtures.ps1            # report-only
.\dottalkpp\scripts\mcc\reset_mcc_fixtures.ps1 -Execute
.\dottalkpp\scripts\mcc\extract_mcc_og.ps1
.\datarun.ps1
```

```text
DOTSCRIPT TRACE scripts\mcc\mcc_build_x32.dts OUT tmp\mcc_x32.log
DOTSCRIPT TRACE scripts\mcc\mcc_build_vfp.dts OUT tmp\mcc_vfp.log
DOTSCRIPT TRACE scripts\mcc\mcc_build_x64.dts OUT tmp\mcc_x64.log
DOTSCRIPT TRACE scripts\mcc\mcc_demo.dts      OUT tmp\mcc_demo.log
```

**The reset is not optional.** `CNX CREATE` and `CDX CREATE` refuse to
overwrite an existing container. If the old containers survive, the "rebuild"
silently degrades into a `REINDEX` of whatever tags happened to be there, and
any tag the script declares is never actually created.

On a virgin run every `CREATE` reports **`created:`**. If you see
**`file already exists`**, the reset did not run.

## Path Rules

Maintainer-declared, 2026-07-14:

- **Two directories minimum before any work: `DBF` and `INDEXES`.**
- Default homes for x32 / vfp / x64 data: `data\dbf\<lane>`
- Index directories: `data\indexes\<lane>`
- Index names match table names
- `data\lmdb` is **x64 only** — no LMDB on the x32 or VFP lanes

Destination paths in `COPY TO` are relative to the **DATA root**:

```text
COPY TO DBF\x32\STUDENTS    ->  data\dbf\x32\STUDENTS.dbf     CORRECT
COPY TO ..\x32\STUDENTS     ->  dottalkpp\x32\STUDENTS.dbf    WRONG
```

Do **not** use `DO X32` from a script in `scripts\mcc\`. The DOTSCRIPT resolver
resolves relative to the *invoking script's* directory, so it cannot see
`data\x32.dts`. It reports the miss and **continues** with the path slots
unchanged. Inline the two `SET PATH` lines instead.

## Index Lanes

| | x32 / VFP (v32) | x64 (v64 / v128) |
| --- | --- | --- |
| Container | **CNX** — sorted index by tag | **CDX** |
| Runtime tag mutation | **NO** — batch rebuild only | **YES** |
| Rebuild | `REINDEX CNX` | `BUILDLMDB` |
| LMDB backing | none | `data\lmdb\x64\<stem>.cdx.d` |

`USE` attaches the right container automatically: *"x64/v128 tables prefer CDX.
x32 tables prefer CNX, then INX."*

`INDEX ON` builds an **INX** file — a different lane. It does **not** build
CDX/CNX tags. `BUILDLMDB` **builds** the LMDB store from a CDX container;
`SETLMDB` only **selects** an already-built one.

## Tags

Harvested from the live containers 2026-07-14 — **not** from the schema notes,
which under-declare. Identical across all three lanes.

| Table | Tags |
| --- | --- |
| BUILDING | BLDG |
| STUDENTS | SID, MAJOR, LNAME, FNAME, DOB, GPA |
| TEACHERS | TID, DEPT_ID, LNAME, FNAME |
| COURSES | CID, DEPT_ID |
| CLASSES | CLS_ID, TERM, CID, ROOM, TID |
| ENROLL | SID, CLS_ID |
| ROOMS | ROOM, BLDG |
| MAJORS | MAJOR, DEPT_ID |
| DEPT | DEPT_ID |
| TERMS | TERM |
| STUD_MAJ | SID, MAJOR |
| TASSIGN | CLS_ID, TID |

**Expression indexes are not a DotTalk++ capability.** `INDEX ON` takes a field
key. The composite tags in the FoxPro-era schema notes (`UPPER(LNAME+FNAME)`,
`TERM+CID+STR(SEC,2)`) cannot be built. See
`docs/contracts/reports/CONTRACT_DRIFT_INDEX_EXPRESSION_2026-07-14.md`.

## Verifying a Run

**A zero exit code is not proof.** The DotScript runner reports unknown commands
and continues to later lines.

**A green readback is not proof either** — this lane learned that the hard way.
On 2026-07-14 three scripts ran clean while writing every table to a junk
directory. The readbacks opened the *old* tables and printed plausible counts.

So every stage asserts the **data**, not just the shape:

```text
virgin STUDENTS : 200 records, record 1 = 50000000 Taylor Quinn
stale  STUDENTS : 201 records, record 1 = 50000000 Taylor Derald
```

If a readback cannot tell you it looked at the right files, it is not a
readback.

| Table | Records |
| --- | --- |
| STUDENTS | 200 |
| TEACHERS | 20 |
| COURSES | 100 |
| CLASSES | 200 |
| **ENROLL** | **686** (the schema notes say "~800" — they are approximate) |
| DEPT | 10 |
| BUILDING | 8 |
| ROOMS | 30 |
| TERMS | 3 |
| MAJORS | 12 |
| STUD_MAJ | 200 |
| TASSIGN | 200 |

`dbf\x64` also holds `TEST64.dbf`, which is not part of MCC — so `WORKSPACE`
reports **13** areas on that lane, not 12.

## Normal Use

```text
USE STUDENTS
SET INDEX TO STUDENTS
SET ORDER TO TAG LNAME

SMARTLIST 10
DESC
SMARTLIST 10
TOP
LIST FOR LNAME = WHITE
```

Then ordinary database operations are available. `mcc_demo.dts` walks this
end to end, read-only.

**Destructive** — never against the sample foundation:

```text
REPLACE LNAME WITH GRIMWOOD
CALC GPA = GPA + 1
```

If you do mutate it, `reset_mcc_fixtures.ps1 -Execute` and rebuild stages 1–3.

## Files

| File | Purpose |
| --- | --- |
| `../../../scripts/mcc/build_mcc_demo_bases.ps1` | **The released entry point.** Warns, shows what will be overwritten, prompts, then builds. |
| `../../../scripts/mcc/reset_mcc_fixtures.ps1` | Virgin slate. Report-only by default. |
| `../../../scripts/mcc/extract_mcc_og.ps1` | Unpack the archive to `dbf\og`. MD5-pinned. |
| `mcc_build_x32.dts` | Stage 1 — og → x32 (MS-DOS) + CNX |
| `mcc_build_vfp.dts` | Stage 2 — x32 → vfp (VFP) + CNX |
| `mcc_build_x64.dts` | Stage 3 — vfp → x64 (X64 VECTOR) + CDX + LMDB |
| `mcc_build_x64_lmdb.dts` | LMDB-only rebuild. LMDB is gitignored, so a fresh clone regenerates it with this. |
| `mcc_demo.dts` | Read-only tour of normal operations |

## Build Status

**Built clean 2026-07-14.** First good run. Evidence:

- every `CNX CREATE` / `CDX CREATE` reported **`created:`** — a real build, not a
  `REINDEX` of stale containers
- every `CDX ADDTAG` reported **`added`** — all 23 tags actually created
- copies landed in `data\dbf\{x32,vfp,x64}` — `Copied table to DBF\x64\STUDENTS.dbf`
- freshness assertion passed on all three lanes: **200 records, `Taylor Quinn`**
- `NOINDEX: auto-attach skipped (physical order)` on every copy source
- `BUILDLMDB` built all 12 envs, no prompts, 128 MiB
- CDX ordering and LMDB ordering **agree** for the same tag
- `SETLMDB 0` → `SET LMDB: cleared (physical order).`

## Known Runtime Observations

Raised for the maintainer; **not** worked around in these scripts.

**`SHOW TABLE` misreports paths.** Two instances in the 2026-07-14 transcripts:

```text
Path : D:\...\dottalkpp\data\STUDENTS         <- missing the dbf\<lane> segment
Index: D:\...\data\indexes\x32\STUDENTS.cnx   <- reported during the VFP readback,
                                                 while PATH INDEXES was INDEXES/vfp
                                                 and WORKSPACE had attached the VFP
                                                 container
```

The behavior is correct — `SET ORDER` and `SMARTLIST` used the right container.
Only the `SHOW TABLE` display is wrong. Cosmetic, but it is exactly the kind of
misreport that sent this lane chasing ghosts for half a day.

**Bare `ASC` does not undo `DESC`.** It takes an argument:
`ASC expects 1 argument(s).` The runner reports the error and continues, so the
table silently stays descending. `SET ORDER TO TAG <tag>` restores ascending.

**`SETLMDB PHYSICAL` is not a valid form.** It fails with
`openCdx: LMDB env missing: ...\PHYSICAL.cdx.d` — `PHYSICAL` is taken as a
container name. `SET LMDB USAGE` gives `SET LMDB 0` to clear ordering. The
form appears several times in
`dottalkpp/data/scripts/canaries/mcc_exhaustive_full_regression_canaries_lmdb.dts`,
where it has been failing silently.

**`BUILDLMDB` and `SETLMDB` report different env directories** for the same
container:

```text
BUILDLMDB: LMDB env   data\LMDB\x64\STUDENTS.cdx.d      <- LMDB slot
SET INDEX: LMDB env   data\LMDB\x64\STUDENTS.cdx.d      <- agrees
SETLMDB:   envdir:    data\INDEXES\x64\STUDENTS.cdx.d   <- disagrees
```

Two of three agree. `SETLMDB` is the outlier.
