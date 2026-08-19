---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-013
  recorded_at_utc: 2026-08-19T00:01:29Z
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
    requested_by: maintainer (member.derald), in-session, "next" -> agent proposed the
      section 7 experiment over gate 10; maintainer ran each MODIFY FORM attempt and
      returned the screenshots that are this document's evidence.
  report:
    path: docs/maintenance/AIF120_GENERATED_SCX_ACCEPTED_V1.md
    kind: ruling
---

# AIF-120 -- R13: VFP 9 opened an x64base-generated form, and what it cost to get there

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

**Evidence tier: `runtime-proven`, witness stated.** Microsoft's Form Designer
opened the file. It was run by the maintainer on `grimwood` and witnessed by the
agent as a screenshot; the agent did not execute VFP. Everything about the file
itself was generated and measured in-session.

## 1. The result

`tools/vfp/generated/X64FORM.SCX` + `.SCT`, written by
`tools/vfp/write_vfp_binary.py` with no VFP involved, opened in
**Form Designer - x64form.scx**, captioned "STUDENTS (x64base-generated)", with
nine label/textbox pairs bound to the nine `STUDENTS` fields -- `Sid/SID1`
through `Email/EMAIL1`. VFP status bar: `Done`.

**And it RUNS.** `DO FORM d:\code\ccode\tools\vfp\generated\X64FORM.SCX`
instantiated the form and bound it to live data. Record 1 on screen, checked
field by field against the table: `50000000 / Taylor / Quinn / 12/25/1992 / X /
CSCI / 02/20/2025 / 2.97 / quinn.taylor0@student.mcc.edu` -- **9 of 9 fields
match**, with `DOB` stored `19921225` rendering `12/25/1992` and `GPA` stored
`2.97` rendering `2.97`.

So the whole chain is now proven end to end against the reference
implementation, with no VFP anywhere in the producing half:

```text
x64base COPY TO ... AS VFP   ->  STUDENTS.dbf   -+
                                                 |-> VFP 9 runtime -> a working,
x64base write_vfp_binary.py  ->  X64FORM.SCX/SCT-+   data-bound form
```

The charter's amendment (b) argues a generator is "a consumer of a table, not of
the parser," and that the design table is the deliverable. **This is the first
evidence that this project can stand on the producing side of that contract**
against the reference implementation rather than against its own tests.

Two consequences beyond the fact:

- **Gate 10 can be validated, not just asserted.** A documented schema is now
  checkable by generating a file and offering it to Microsoft's designer. That is
  a materially stronger acceptance test than internal review.
- **R12's partial geometry is accepted by a real consumer.** Measured on the
  accepted file after VFP released it: **19 geometry-bearing records, 19 of them
  partial** -- `label` x9 and `textbox` x9 carry `Left`/`Top`/`Width` and no
  `Height`, and the `form` carries `Height`/`Width` and no `Top`/`Left`. The
  designer laid all of them out. Partiality is not merely something a producer
  emits and a permissive reader tolerates; the reference implementation resolves
  it, at 100 percent of records in this file.
- `CLASSLOC` is empty in all 23 records, so the accepted file is self-contained
  under R1 and needed no `.VCX` on the opening machine.

## 2. R13 -- the ruling

**R13. The designer formats have required-on-output fields that are optional on
input. A schema that records only "required / optional" is insufficient; the
design table contract must record required-ness PER DIRECTION.**

This was not visible from reading. It cost two rejections to find, each fixed by
exactly one change, so each is a cause and not a correlation.

| # | VFP 9 error | Cause | Fix |
| --- | --- | --- | --- |
| 1 | `record number 2. Dataenvironment <or one of its members>. Parent : Class name is invalid` | `CLASS` left empty on every record | populate `CLASS`; where there is no styling class it repeats `BASECLASS` |
| 2 | `record number 5. LBLSID <or one of its members>. Parent : Object class is invalid for this container` | `RESERVED2` omitted on the DataEnvironment record | write the definition-block record count (`2` = the record plus its one cursor) |

**On error 1.** R1 rules "key the importer on `BASECLASS`; treat `CLASS` as an
optional theme hint." True, and it made me omit `CLASS` on output. Measured
afterwards: `CLASS` is non-empty in every record of all three specimens, and the
NATIVE `form1.scx` sets `CLASS = BASECLASS` where nothing styles the control --
so this is the format's convention, not a wizard habit. R1 is unchanged as an
import rule and was never an export rule.

**On error 2.** `RESERVED2` is documented in KB Q145742 as counting "records
associated with a class definition," and measures as `2` on the DataEnvironment
record of all three specimens. Omitting it appears to leave the DataEnvironment
block unterminated, so the form record is absorbed into it and the first label's
container is a `dataenvironment` -- for which "Object class is invalid for this
container" is exactly right. Setting `RESERVED2` alone, with every other byte
unchanged, made the form open. **Mechanism proposed before the test, confirmed
by it.**

## 3. The methodological finding, which outlasts the format

Three properties of `.SCX` that three days and three specimens of *reading* did
not surface:

1. `CLASS` required on output (found by writing)
2. `RESERVED2` as a block-length count (found by reading Microsoft's KB)
3. the font metrics table in the trailing `RESERVED` record (found by reading raw
   records to build a writer; retracts R12's M5)

**Reading a format teaches what a producer happened to emit. Writing it teaches
what a consumer actually requires.** The two are different sets, and this lane
spent its first three days measuring only the first while believing it was
characterising the format. Every open question that a specimen could not settle
should now be asked in the form "what happens if we generate it and hand it
back," because that question has a referee and specimen-reading does not.

The corollary is uncomfortable and worth writing down: the lane had access to
Microsoft's published table-structure documentation and to `FILESPEC\90SCX.dbf`
-- a DBF of the specification, readable by this project's own reader, shipped
inside the VFP install on this machine -- and used neither until day three.
**The authoritative source was never consulted because three files and a reader
felt like enough.**

## 4. What this does NOT establish

- ~~**The form was opened, not run.**~~ **Settled the same session:** `DO FORM`
  instantiated it with live data, 9 of 9 fields verified. See section 1.
- **No save round-trip.** If the designer saves, VFP rewrites the file, and
  whether our record set survives that is unknown and is the next cheap test.
- ~~**`OBJCODE` is still empty** and still untested.~~ **Settled:** `OBJCODE` is
  non-empty in **0 of 23** records, and both the designer AND the runtime
  accepted the file. Neither requires compiled p-code for a form of this shape.
- **Easy vocabulary only.** Labels, textboxes, one container-free form. R6's
  implicit children (grids, pageframes, option groups) and R7's OLE are untouched.
- **One machine, one VFP 9 install.** Not a regression test; nothing will notice
  if a future change breaks it.

## 4b. A portability gap the run exposed, and it is the format's, not ours

`DO FORM` could not find the table until the maintainer located it by hand,
because nothing had run `SET PATH`. The reflex is to call that a defect in this
writer. Measured, it is not:

| | `CursorSource` |
| --- | --- |
| our generated form | `students.dbf` |
| VFP 9's own wizard form | `students.dbf` |

**Identical.** Matching the wizard is the correct behaviour for this writer, so
nothing here should be "fixed".

> **CORRECTED by the save round-trip, section 6.** The conclusion first drawn
> here -- "the format addresses its data source by bare filename and relies on
> ambient state, and ambient state does not travel" -- is **wrong**. When VFP
> saved the form it rewrote `CursorSource` to
> `..\..\..\dottalkpp\data\dbf\vfp\students.dbf`: a path **relative to the
> `.SCX` itself**. The bare filename is the degenerate same-directory case, not
> the format's addressing model. The format's model is relative-to-document,
> which is the same mechanism as R1's `CLASSLOC` (`..\..\..\..\..\program
> files (x86)\...`), and it **does** travel. Gate 10 should adopt it rather than
> invent an alternative. Recorded here rather than deleted because the sequence
> is the point: one save answered a question that reading three specimens had
> answered wrongly.

## 6. The save round-trip: VFP as oracle

The decisive test. Baseline preserved in `tools/vfp/generated/presave/`, form
opened in the designer, one control nudged and returned, `Ctrl+S`, closed. VFP
rewrote both files (and lowercased their names to `x64form.scx` / `.SCT`).

**What VFP did NOT change -- the validation.**

| | ours | after VFP save |
| --- | --- | --- |
| version / `hlen` / `rlen` | `0x30` / 1032 / 109 | identical |
| field definitions (23) | | **byte-identical** |
| record count | 23 | 23 -- none added, none removed |
| record order | | unchanged |
| all 18 label/textbox `PROPERTIES` | | **byte-identical** |

Our table shape is not merely tolerated; the reference implementation reproduces
it exactly.

**R12.3 is now proven as strongly as this lane can prove anything.** The 18
controls carry `Left`/`Top`/`Width` and no `Height`. VFP loaded them, rendered
them, ran them, and **wrote them back still partial** -- not one `Height` added.
Partial geometry survives a full round trip through Microsoft's own designer
untouched. It is the format's normal state, not a defect a real consumer repairs.

**What VFP did change -- four gaps in our writer, named by the reference.**

| # | where | ours | VFP | reading |
| --- | --- | --- | --- | --- |
| 1 | `TIMESTAMP`, every object record | blank | `0` on the DataEnvironment, `1561496112` on cursor/form/controls | blank is accepted on input; VFP always emits a value |
| 2 | `CursorSource` on the cursor | `students.dbf` | `..\..\..\dottalkpp\data\dbf\vfp\students.dbf` | **relative-to-document addressing** -- see the correction in 4b |
| 3 | `PROPERTIES` on `form` | no `Top`/`Left` | adds `Top = 0`, `Left = 0` | containers get geometry normalised; controls do not |
| 4 | `RESERVED4` on the DataEnvironment | empty | `1` | **an undocumented column with a meaning we do not know.** Not in KB Q145742. Named here as an open question rather than guessed at |

### 6b. The addressing rule, proved by accident

The maintainer's session also saved the form a second time, one minute later,
from `dottalkpp/data/dbf/vfp/` -- the directory the table itself lives in. That
turned an inference into a controlled experiment: same form, same table, two
locations, one variable.

| the `.SCX` lives in | VFP writes `CursorSource` as |
| --- | --- |
| `tools/vfp/generated/` | `..\..\..\dottalkpp\data\dbf\vfp\students.dbf` |
| `dottalkpp/data/dbf/vfp/` (same dir as the table) | `students.dbf` |

Everything else in the two files is identical apart from `TIMESTAMP`. **VFP
recomputes the data-source path relative to the `.SCX` on every save.** The bare
filename is not a fallback to ambient state; it is the correct relative path when
the distance is zero -- which also retroactively explains why VFP's own wizard
form carried a bare `students.dbf`: the wizard wrote it next to the table.

Two consequences. The format is **idempotent** across saves except for
`TIMESTAMP` and this recomputed path, so a round-trip test can assert equality on
everything else. And gate 10 has its addressing answer measured rather than
designed: relative-to-document, recomputed on write.

Both files are kept as `X64FORM_VFPSAVED.*` and `X64FORM_SAMEDIR.*`.

Gap 3 is the sharpest single observation in this document: **VFP normalises
geometry on containers and leaves it partial on controls.** That is a rule, it is
measured, and no amount of reading the three specimens would have distinguished
it from "wizards happen to emit it that way."

## 5. Next, in cost order

1. ~~`DO FORM` -- does it run and show data?~~ **Done, it does.** See section 1.
2. ~~Save from the designer, then diff.~~ **Done -- section 6.** Four gaps found,
   one of them (`RESERVED4`) still unexplained.
3. Point the reader at `FILESPEC\90SCX.dbf` and read the specification itself.
4. Only then write gate 10's schema, with `R13`'s per-direction requiredness in
   it from the start rather than added after.

## 6. Handoff -- PowerShell, run in `D:\code\ccode`

Note on the lock: VFP held `X64FORM.SCX` while the designer was open and released
it on restart. Verified after release -- **the designer did not rewrite the file**:
mtime is still the generation time and the bytes are the generated bytes
(`sha256 9d60e6a39eb6c0c8`, `.SCT` `22f3a7430eff3b85`). Opening is non-mutating;
saving, which is test 2 in section 5, is a separate question.

```powershell
git add docs/maintenance/AIF120_GENERATED_SCX_ACCEPTED_V1.md
git add tools/vfp/write_vfp_binary.py tools/vfp/make_students_form.py
git add tools/vfp/generated/X64FORM.SCX tools/vfp/generated/X64FORM.SCT
git add tools/vfp/generated/OPENX64FORM.PRG
git status --short -uall
git commit -m "AIF-120: R13 -- VFP 9 opened an x64base-generated .SCX; required-on-output fields are not required-on-input"
```
