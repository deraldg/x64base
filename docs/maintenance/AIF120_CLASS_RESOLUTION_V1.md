---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-039
  recorded_at_utc: 2026-08-19T12:50:00Z
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
    requested_by: maintainer (member.derald), in-session, "yes we must continue" --
      mechanism A, the half R30 left unsolved.
  report:
    path: docs/maintenance/AIF120_CLASS_RESOLUTION_V1.md
    kind: ruling
---

# AIF-120 -- R31: a `.VCX` is a sequence of class blocks, and an instance is flattened

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R30 split the dotted property names into two mechanisms and solved the smaller
one. This solves the larger: 637 member names behind 118 class references, in a
format the lane had measured as a container and never read as a library.

## 1. R31.1 -- the block structure

A `.VCX` is not a flat table of objects. It is a sequence of **class definition
blocks**:

```
rec 10  WINDOWS  vcr           PARENT=          RESERVED2=6
rec 11  WINDOWS  cmdTop        PARENT=vcr
rec 12  WINDOWS  cmdPrior      PARENT=vcr
rec 13  WINDOWS  cmdNext       PARENT=vcr
rec 14  WINDOWS  cmdBottom     PARENT=vcr
rec 15  WINDOWS  Datachecker1  PARENT=vcr
rec 16  COMMENT  vcr                            <- block terminator
```

One root record with an empty `PARENT` and a `RESERVED2` giving the number of
records in the block including itself; `RESERVED2 - 1` members; a `COMMENT`
record repeating the name.

Measured: **25 libraries, 110 live classes, 0 declared-count mismatches.** Every
block in the corpus has exactly the records it declares.

`RESERVED2` earns its third appearance in this lane. R13 found it holding "this
record plus its one cursor" in an `.SCX`; R30.1 used `buttoncount`; here it is a
block length. **The format keeps telling you how many records to expect, and this
lane keeps finding that checking it is free.**

## 2. R31.2 -- resolution is by block and liveness, never by name

`solution.vcx` contains **three** blocks named `frmsolution` and **two** named
`c_solutions`. Matching on name picks an arbitrary one.

Two of each are **deleted**. VFP appends a new block when a class is edited and
marks the old one deleted, so the live block is the answer.

| extension | live records | deleted |
| --- | --- | --- |
| `.vcx` | 457 | **206 (31%)** |
| `.scx` | 3,350 | **0** |
| `.mnx` | 261 | 0 |
| `.frx` | 521 | 0 |

`read_vfp_binary.py` has always yielded deleted rows with a `_DELETED` flag the
callers ignore. **That was harmless for every measurement this lane has made,
because forms and menus in this corpus contain no deleted records** -- I checked
rather than assumed, and R19 through R30 are unaffected. It stops being harmless
the moment you open a class library, where nearly a third of the file is history.

> **R31.2.** A class is resolved by locating its block by declared length and
> taking the last **live** block of that name. A name alone does not identify a
> class.

Same shape as R18: never infer structure from a field the format lets repeat or
leave blank. There it was `.MNX` nesting; here it is class identity.

## 3. R31.3 -- flatten, and record that you flattened

An instance's class members are materialised into the document as ordinary rows
with the instance's dotted properties applied as overrides.

- The design table stays **self-contained**. A consumer draws a form without a
  `.VCX` reader, which is what section 1 of the contract promises and what gate 11
  measured it failing to deliver.
- `PROVENANCE` gains a third value, **`inherited`**, beside `authored` and
  `imported`. A vocabulary extension, not a schema change.
- The instance keeps `Class` and `ClassSource` in `PROPS` as named keys (R25.5),
  so the flattening is reversible and an exporter can fold it back.

Instance overrides win over class defaults, which is what an override is.

## 4. R31.4 -- addressing, and our own specimen fails it

`CLASSLOC` is resolved **relative to the document** (4b, R12), with a
case-insensitive retry for the reason R28.3 gave. An absolute path is refused
rather than tried.

Measured `CLASSLOC` in the corpus: **412 relative, 19 bare, 0 absolute.** Real
third-party forms are portable.

`STUDENTS.SCX`, this lane's own form-wizard specimen, is not. **All 20 of its
objects are subclassed**, from four wizard classes at

```
c:\program files (x86)\microsoft visual foxpro 9\wizards\wizembss.vcx
c:\program files (x86)\microsoft visual foxpro 9\wizards\wizbtns.vcx
```

Nobody without VFP 9 installed at that path can resolve them. The importer now
refuses all four by name rather than dropping them silently. This is the third
time a portability rule has been broken by a fixture this lane produced and kept
by the corpus it borrowed -- 4b's addressing, R31's absolute paths, and the
`/tmp/gen` entries R23 swept up.

## 5. Measured, corpus-wide

| | |
| --- | --- |
| class references | 431 |
| **resolved** | **351 (81%)** |
| **inherited members materialised** | **363** |
| `OBJ` rows: before R30 / after R30 / after R31 | 2,186 / 2,324 / **2,687** (+23%) |
| dotted names still unresolved | 274 -- libraries absent from the corpus |
| refusals, all named | 45, all "not found relative to the document" |

`frmsolution` alone accounts for 288 materialised members across the corpus, and
`vcr` -- a record-navigation container, the same shape as the `txtbtns` panel gate
11 found empty -- for 56.

## 6. Still open

- **One level.** A class member that is itself an instance of another class is not
  recursed. The rule is the same; the implementation stops at depth one and says
  nothing about it, which it should.
- **Methods are not inherited.** R14 keeps bodies out of v1, so a class's
  `METHODS` are ignored entirely. A handler reference defined only on a class is
  therefore lost, and nothing counts it.
- **No round trip.** Nothing folds `inherited` rows back into dotted properties on
  export.
- **The 274 unresolved** need libraries the corpus does not contain. Whether the
  design table should be able to carry a class library at all -- rather than
  flattening every instance -- is a real design question this ruling ducks by
  always flattening.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_CLASS_RESOLUTION_V1.md
git add docs/maintenance/evidence/AIF120_classlib.txt
git add gui/uidef/classlib.py
git add gui/uidef/import_scx.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R31 -- .VCX read as a class library; 363 inherited members materialised, 81% of class references resolved"
```
