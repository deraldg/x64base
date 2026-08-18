---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260818-COWORK-008
  recorded_at_utc: 2026-08-18T17:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 6d52c6d6f
  authorization:
    requested_by: maintainer (member.derald), in-session, "document our findings so far - remind me if we have a lane and an aif for our gui api"
    scope: >
      Lane and AIF identity for the GUI API work, the specimen fixture manifest,
      and a pointer table to where each finding is maintained. Deliberately does
      NOT restate the findings themselves.
  report:
    path: docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
    kind: status-index
---

# AIF-120 -- lane status, and where the GUI API findings live

Status: index, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Date: 2026-08-18.

**This file points; it does not restate** (AIF-082, 6.8: two documents that
restate each other diverge, and have). Findings are maintained in the two files
in the pointer table below. What is recorded HERE and nowhere else is the lane
identity, the fixture manifest, and the settled/open ledger.

## Yes, both exist. Measured 2026-08-18, not recalled.

| what | value | where it is recorded |
| --- | --- | --- |
| **Lane** | `application-ui-dsl` | charter: `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md` |
| **AIF** | **AIF-120** | claim: `coordination/aif/AIF-120.claim` |
| claimed | 2026-08-18T03:15:29Z | same |
| claimed by | `member.ai.claude.cowork` | same |
| run id | `COWORK-20260817-001` | same |
| portal registration | present | `labtalk/ai_portal/TIER0_STATE.md:37` |

The sibling lane chartered the same session is **AIF-119**, pydottalk as a
co-sourced product. `TIER0_STATE.md:63` records this run as `AIF-119 -> AIF-120`.

A caution about how that was checked: a recursive `grep` over `docs/maintenance`
**exits 124 (timeout) in the sandbox and prints nothing**, which is
indistinguishable from "no matches" unless the exit code is read. The first pass
of this check reported AIF-120 as registered nowhere. Name the files instead of
recursing that directory.

## Pointer table -- where each finding is maintained

| subject | file |
| --- | --- |
| Lane charter, scope, proof gates, and rulings **R1 through R12** | `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md` |
| **R11, the threading ruling (gate 9)** -- full text, evidence, disproof conditions | `docs/maintenance/AIF120_THREADING_RULING_V1.md` |
| **R12, the coordinate ruling (gate 8)** -- six measurements, disproof conditions | `docs/maintenance/AIF120_COORDINATE_RULING_V1.md` |
| **VFP 9 reading an x64base-written table** -- the lane's first `runtime-proven` result | `docs/maintenance/AIF120_VFP_READS_X64BASE_OUTPUT_V1.md` |
| The shipped GUI core the ruling adopts | `src/gui/core/`, `include/gui/core/`, `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md` |
| Specimen-by-specimen measurements and the corrections between them | `docs/maintenance/AIF120_VFP_SCX_EMPIRICAL_BASELINE_V1.md` |
| The reader that produced every measurement | `tools/vfp/read_vfp_binary.py` |
| Specimen files | `tools/vfp/fixtures/` (manifest below) |

## Fixture manifest

The specimens arrived as chat uploads, which are **ephemeral**. They are the
input/output evidence for every ruling in the charter and for any future
round-trip test, so they are copied into the tree here. 91 KB total.

| file | bytes | sha256 (first 16) | what it is evidence of |
| --- | --- | --- | --- |
| `ACCOUNTS.DBF` | 616 | `8624e4cdd33ff662` | empty 10-field table, 6 of 7 x64base field types; schema donor for the form |
| `ACCOUNTS.FPT` | 512 | `b11162605d45a90c` | its memo sidecar |
| `ACCOUNTS.SCX` | 3867 | `16dac98f942b4fda` | wizard CRUD form: `CLASS` vs `BASECLASS`, external `.VCX`, `ScaleMode` present |
| `ACCOUNTS.SCT` | 8404 | `dd0f7514f8e53ca5` | its memo sidecar |
| `form1.scx` | 4521 | `48e62f2b60c2e65e` | native-baseclass form: 24 base classes, dotted `PARENT`, implicit children, OLE |
| `form1.SCT` | 8700 | `21cc078e5c8f480b` | its memo sidecar |
| `test_go.mnx` | 2189 | `c283d75443fcc23b` | smallest menu; the one round-tripped against its `.MPR` |
| `test_go.mnt` | 1914 | `06a8b65829fab5c1` | its memo sidecar |
| `test_main.mnx` | 7181 | `c939c27fa5772019` | full menu vocabulary, 10 containers |
| `test_main.mnt` | 12111 | `365ce64c631f7d50` | its memo sidecar |
| `test_top.mnx` | 7181 | `eead3c80bf326ca2` | 10 containers |
| `test_top.mnt` | 10395 | `333c3ff5f8edc8ae` | its memo sidecar |
| `test_append.mnx` | 3827 | `ed2f9fdd6c6da6d2` | 5 containers |
| `test_append.mnt` | 5148 | `0d74c5b30dd57a2c` | its memo sidecar |
| `TEST_GO.MPR` | 3210 | `152157bd17e456a8` | **GENMENU output for `test_go.mnx`** -- the reference the DSL is checked against |
| `TEST_MAIN.MPR` | 13709 | `f57f4679843ab19b` | GENMENU output showing the imperative half of the vocabulary |

**All sixteen landed.** `ACCOUNTS.SCX`/`.SCT` arrived last, after VFP released
them; the fourteen others copied while the form was still open in the designer.

That lock behaviour is worth recording, because it **inverted twice in one day**:
in the morning `ACCOUNTS.DBF`/`.FPT` were locked while `.SCX`/`.SCT` read fine
(table open, form closed); in the afternoon the reverse (form open in the
designer, table closed); then neither. Tooling that reads a live VFP working set
must expect either half of a pair to be unavailable and **must not treat a failed
open as an absent file** -- the same conflation AIF-118 names, arriving through
the filesystem instead of through a check.

**The bytes were verified unchanged, not assumed.** VFP held `ACCOUNTS.SCX` open
in the Form Designer for several hours between the morning measurement and this
copy, and a designer that saves on close would have replaced the file the
findings were drawn from. All four ACCOUNTS files hash identical to the copies
taken before VFP opened them, so every measurement in the baseline file stands on
the same byte stream that is now in `fixtures/`. Had they differed, the specimen
sections would have needed re-running rather than re-labelling.

The `.MPR` pair matters more than its size suggests: **`test_go.mnx` and
`TEST_GO.MPR` are a free input/output fixture.** A menu generator written for
this lane can be diffed against Microsoft's own GENMENU output rather than
against opinion. Two fidelity notes apply and are recorded in the baseline file.

## Settled / open ledger

Settled, with the ruling text in the charter:

| id | one line | specimen that settled it |
| --- | --- | --- |
| R1 | key the importer on `BASECLASS`, not `CLASS` | ACCOUNTS + form1 |
| R2 | the DSL carries an explicit scale mode, and a default when absent | ACCOUNTS (present) + form1 (absent) |
| R3 | property import is an allow-list, never a deny-list | ACCOUNTS |
| R4 | `.SCX` import recovers layout and binding, not logic -- **and this is a property of wizard files, not of the format** | ACCOUNTS + form1, corrected by the menus |
| R5 | identity is the dotted path, never `OBJNAME` | form1 |
| R6 | count properties create children that no record describes | form1 |
| R7 | `olecontrol` / `oleboundcontrol` out of scope, stated not discovered | form1 |
| R8 | the menu DSL already exists as text; adopt, do not invent | the `.MNX` + `.MPR` set |
| R9 | menu scope splits declarative / imperative; charter must pick | TEST_MAIN.MPR |
| R10 | every designer format parents differently; only the DBF layer is shared | all three |
| R11 | UI-thread rule adopted from the shipped GUI core; table carries `DISPATCH` with default `ui`, `worker` requires `ON_COMPLETE` | `src/gui/core/` + `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md`, not a specimen |
| R12 | layout intent is the portable geometry; absolute coordinates quarantined, advisory, and carrying R2's unit | the wx frontend, the GUI core, 205 menu records, 58 form records |

Open:

- ~~**The threading ruling.**~~ **Closed 2026-08-18 as R11**, run
  `COWORK-20260818-001`, review-needed. It was never open in the way this list
  said: the rule was already written and shipped in `src/gui/` and `docs/ui/`,
  and this file's own claim that no measurement had touched it was produced by a
  search shaped for `DEFINE WINDOW`. See the ruling's section 0.
- ~~**`docs/ui/` is untracked.**~~ **Closed**: fixed in `1a40c97a7`, "docs/ui:
  track the four active UI architecture documents (widow fix)". Verified
  2026-08-18 by run `COWORK-20260817-001`: 4 of 4 in the index AND 4 of 4 in
  `HEAD`, working tree clean.

  **Amended by run `COWORK-20260818-001`, the run that reported it.** The item is
  closed, but not because the original check was wrong -- the maintainer acted on
  the report. Sequence, measured from the log rather than recalled: the report was
  made at baseline `6d52c6d6f`, where `git ls-tree -r 6d52c6d6f -- docs/ui`
  returns **0 files**; `1a40c97a7` then adds all four with status `A`, which is
  git's own statement that they were in no prior commit; its author is
  `Derald Grimwood` and its timestamp is 08:25:51 -0700, six minutes after the
  report. The widow was real, and reporting it is what closed it.

  The general caution above is worth keeping and is separately true: `git
  ls-files` reads the index, so for a claim of the form "this file is in no
  commit", `ls-tree HEAD` is the check that matches the claim. It did not apply
  to this instance -- `ls-files docs/ui` returned **0**, and an empty index
  result cannot be a staged-but-uncommitted false positive; only a non-empty one
  can. Recording the check as inadequate when it was sound would teach the wrong
  lesson in a house whose rules are earned by real failures.
- ~~**The coordinate fork.**~~ **Closed 2026-08-18 as R12**, run
  `COWORK-20260818-001`, review-needed: option 3, layout intent primary.
  Like the threading item, it was less open than this list said -- the four
  `.MNX` specimens carry 205 records and zero geometry columns, so the menu half
  of the fork had already been decided by R8's adoption of that vocabulary.
- **A hand-authored `.SCX` with real method code.** Both form specimens are
  designer output. The menus proved the reader extracts code, so this is no
  longer urgent -- it is now about vocabulary in `METHODS`/`OBJCODE`, not about
  whether extraction works. **Its value rose with R12:** it is also disproof
  condition 4 for the coordinate ruling, since a hand-authored form declaring all
  four dimensions on every control would show R12's measured partiality (22 of 45
  records) as a wizard artifact rather than a property of the format. One
  specimen now tests two rulings.
- ~~**`ACCOUNTS.SCX` / `.SCT` into fixtures.**~~ **Closed**: VFP released them
  and all sixteen fixtures are present and hash-verified, as the manifest above
  already recorded. This entry contradicted its own document for one edit cycle
  -- two runs amended the same uncommitted file and neither reconciled the other
  half. Worth noting as the concrete cost of concurrent editing that AIF-050
  warns about: nothing was lost, but the file asserted both "all sixteen landed"
  and "two still pending" simultaneously.

## One measurement runs the other way

Everything in the settled ledger above was produced by reading files VFP wrote.
On 2026-08-18 the direction reversed for the first time: VFP 9 opened
`dottalkpp/data/dbf/vfp/STUDENTS.dbf` -- written by this project's own
`COPY TO ... AS VFP` at `dottalkpp/data/scripts/mcc/mcc_build_vfp.dts:81` -- read
all 200 records, and agreed with `tools/vfp/read_vfp_binary.py` on all 81 field
values legible in the witness screenshot. Header measured genuinely VFP:
`hlen` 584, which is the plain 321 for nine fields plus VFP's 263-byte backlink
block.

It is the lane's only `runtime-proven` result and the referee was Microsoft's
implementation rather than this project's test suite. It is also one interactive
session on one machine, proving nothing about `.SCX`, about writing, about
indexes, or about the four untested field types. Both halves are recorded in
`docs/maintenance/AIF120_VFP_READS_X64BASE_OUTPUT_V1.md`.

## The honest summary of this measurement lane

Three specimen sets over two days produced ten rulings, and **four of them exist
because an earlier claim of mine was wrong and the next specimen said so**: the
"not self-contained" generalisation, the "real files declare their scale mode"
generalisation, the "unresolved parents come from the class library" explanation,
and the near-miss of writing R4 into the charter as a format limitation. Each was
stated confidently from one file. The specimens were cheap and the corrections
were free; had any of them reached the charter unchallenged, they would have been
expensive.

The practical lesson for the rest of this lane: **one file is not a format.**
