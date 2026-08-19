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
| Lane charter, scope, proof gates, and rulings **R1 through R12** -- amendments (a) to (e) | `docs/maintenance/APPLICATION_UI_DSL_LANE_V1.md` |
| Rulings **R13 through R29** live in their own files; this ledger is their only index. The charter does not carry them. | -- |
| **R11, the threading ruling (gate 9)** -- full text, evidence, disproof conditions | `docs/maintenance/AIF120_THREADING_RULING_V1.md` |
| **R12, the coordinate ruling (gate 8)** -- six measurements, disproof conditions | `docs/maintenance/AIF120_COORDINATE_RULING_V1.md` |
| **VFP 9 reading an x64base-written table** -- the lane's first `runtime-proven` result | `docs/maintenance/AIF120_VFP_READS_X64BASE_OUTPUT_V1.md` |
| **STUDENTS.SCX**, third form specimen; replicates R1/R2/R4/R12.3 and corrects R12's M4 | `docs/maintenance/AIF120_STUDENTS_SCX_SPECIMEN_V1.md` |
| **R13** -- VFP 9 opened an x64base-GENERATED `.SCX`; required-on-output vs required-on-input | `docs/maintenance/AIF120_GENERATED_SCX_ACCEPTED_V1.md` |
| The writer that produced it | `tools/vfp/write_vfp_binary.py`, `tools/vfp/make_students_form.py` |
| **First `.VCX`** -- scale mode as a word in `RESERVED6`; `RESERVED2` corroborated; vocabulary 24 -> 26 | `docs/maintenance/AIF120_VCX_SPECIMEN_V1.md` |
| **Corpus scan** -- 170 third-party forms, 3,010 records; R13 and M5 confirmed at scale, M4 corrected again, `.FRX` measured | `docs/maintenance/AIF120_CORPUS_SCAN_V1.md` |
| **R14** -- method bodies stay out of v1; 88% of 1,583 real procedures navigate the object model | `docs/maintenance/AIF120_METHOD_CODE_SCOPE_V1.md` |
| **R15** -- three of four formats share a `name = value` property language AND its key vocabulary; gate 10 adopts it | `docs/maintenance/AIF120_SHARED_PROPERTY_LANGUAGE_V1.md` |
| **GATE 10 DRAFT** -- the UIDEF design table as a standalone contract (forms and menus) | `docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md` |
| **UIDEF first implementation** -- writer, importer, validator; three defects found in the contract by producing from it | `docs/maintenance/AIF120_UIDEF_FIRST_IMPLEMENTATION_V1.md` |
| **GATE 11 SPIKE** -- a Tk frontend built from the UIDEF table alone; truncated labels are R12's argument rendered | `docs/maintenance/AIF120_GATE11_TK_SPIKE_V1.md` |
| **R16** -- a stated dimension is advisory when content determines it; A/B render evidence | `docs/maintenance/AIF120_ORIGIN_AB_RULING_V1.md` |
| **R17** -- a BOUND control's width is in the data schema, not the design; r=0.998 on two forms | `docs/maintenance/AIF120_BOUND_WIDTH_RULING_V1.md` |
| **R18** -- `.MNX` submenu links resolve by `OBJCODE 77` + document order, never by name; contract s11 exercised | `docs/maintenance/AIF120_MENU_NESTING_RULING_V1.md` |
| **R11 + R14 verified at runtime** on Tk; `FLOW` and `PROVENANCE=authored` exercised for the first time | `docs/maintenance/AIF120_DISPATCH_RUNTIME_V1.md` |
| **R19** -- `FLOW=free` is what most real forms ARE; 5b's framing withdrawn | `docs/maintenance/AIF120_FLOW_INFERENCE_V1.md` |
| **R20** -- `OBJCODE 78` decoded: a menu item can reference a HOST capability; `DISPATCH` gains `host` | `docs/maintenance/AIF120_HOST_CAPABILITY_RULING_V1.md` |
| **R21** -- serialization is per handler and navigation-triggered; R11.4 contention and lifetime runtime-proven | `docs/maintenance/AIF120_SERIALIZATION_RULING_V1.md` |
| **R22** -- the host capability mapping, its caption guard, and refusal as a visible outcome | `docs/maintenance/AIF120_CAPABILITY_MAPPING_V1.md` |
| **R23** -- `FLOW` belongs to the container; `grid` must state `Columns`; R19's corpus figures corrected | `docs/maintenance/AIF120_FLOW_CONTAINER_RULING_V1.md` |
| **R24** -- a document manifest answers refusal from the table; `FONTREF` resolves the object's own font; `pageset` renders | `docs/maintenance/AIF120_MANIFEST_AND_FONTREF_V1.md` |
| **R25** -- a bound control's width follows its INPUT MASK; R17 narrowed; `PROPS` gains `Mask` | `docs/maintenance/AIF120_MASK_WIDTH_RULING_V1.md` |
| Tab order: measurement only, deliberately rules nothing -- inputs for the owner decision R25 raised | `docs/maintenance/AIF120_TAB_ORDER_MEASUREMENT_V1.md` |
| **R26** -- the unit of serialization is the RELATION SET, not the work area | `docs/maintenance/AIF120_RELATION_SET_RULING_V1.md` |
| **R27** -- tab order becomes `TABORDINAL`, a second ordinal column; the owner's decision | `docs/maintenance/AIF120_TAB_ORDINAL_RULING_V1.md` |
| **R28** -- gate 11 run by an independent implementer: 4 of 5 tables render, 4 contradictions and 19 gaps | `docs/maintenance/AIF120_GATE11_ACCEPTANCE_V1.md` |
| **R29** -- implicit children are 26% of all objects, not an edge case; the importer names what it drops | `docs/maintenance/AIF120_IMPLIED_CHILDREN_V1.md` |
| The UIDEF tooling | `tools/uidef/uidef.py`, `import_scx.py`, `import_mnx.py`, `uidef_tk.py`, `uidef_tk_menu.py`, `author_uidef.py`, `dispatch_test.py`, `infer_flow.py`, `contend_test.py`, `lifetime_test.py`, `uidef_tk_host.py`, `author_flow.py`, `manifest.py`, `author_fonts.py`, `author_tabs.py`, `relate_test.py` |
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
| `STUDENTS.SCX` | 3649 | `d7e0e4df48b6c05f` | **third form**: wizard CRUD over an x64base-written table; the wizard/native partiality split |
| `STUDENTS.SCT` | 7489 | `6caf0899fd045dc0` | its memo sidecar |
| `X64FORM_VFPSAVED.SCX` | 3540 | `43e53d2c1640ab3d` | **x64base-generated, then saved by VFP 9** -- the free input/output fixture for the writer |
| `X64FORM_VFPSAVED.SCT` | 3979 | `801f76d823867269` | its memo sidecar |
| `X64FORM_SAMEDIR.SCX` | 3540 | `8ceac98c1146d58d` | the SAME form saved by VFP from the table's own directory -- `CursorSource` collapses to a bare filename; the controlled pair that proves relative-to-document addressing |
| `X64FORM_SAMEDIR.SCT` | 3947 | `c2c530320a84a898` | its memo sidecar |
| `TEST_APP.VCX` | 4193 | `f103f811a8415e3c` | **first class library**: 14 class stubs, `RESERVED6 = Pixels`, base classes `toolbar` and `custom` |
| `TEST_APP.VCT` | 23349 | `4f34842166c1a4e2` | its memo sidecar |

**All twenty-four landed** (sixteen on 2026-08-18 morning, `STUDENTS.SCX`/`.SCT` that afternoon). `ACCOUNTS.SCX`/`.SCT` arrived last, after VFP released
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
| R13 | the designer formats have required-on-OUTPUT fields that are optional on input; the contract must record requiredness per direction | two VFP 9 rejections, each fixed by one change, then an open |
| R14 | method bodies never enter v1; the table carries a handler REFERENCE, never handler source | 1,583 procedures across 169 corpus forms, 88% object-model-navigating |
| R15 | two shared layers, not one -- the DBF container AND a `name = value` property language with shared keys; R10 amended on payload, unchanged on structure | 3,517 property-bearing records across `.SCX`/`.VCX`/`.FRX`; 9 shared cursor keys |
| R16 | a stated dimension is advisory for content-sized controls, authoritative for data-sized ones; refines R12.3 | two conformant renders of one document, side by side |
| R17 | a bound control's width derives from its field's declared width in characters; the table need not carry it | r=0.9982 (STUDENTS, n=9) and r=0.9977 (ACCOUNTS, n=8); five renders |
| R18 | a structural link must never be inferred from a field the format lets be blank; `.MNX` nesting is `OBJCODE 77` + document order | 1 of 1 and 9 of 9 linked; 2 of 9 openers have an empty NAME |
| R19 | `free` + `ORIGIN` is the correct representation of most imports, not a fallback; 84% of real groups are not row/column/grid | 228 container groups, strict inference: 16% expressible |
| R20 | a menu item may select a capability the HOST provides; `DISPATCH` gains `host`, needing no thread rule and no registry | `OBJCODE 78` on 21 of 67 items; prefix families map 1:1 onto `OBJCODE` |
| R21 | the unit of serialization is the handler, not the cursor operation, and navigation triggers it, not mutation; a completion is delivered at most once | per-op locking 200/200 wrong walks, same as no lock; 0-ms buffer keeps the write and still loses the walk 200/200; corrupt walk reports 100 of 200 students at mean 2.92 vs 2.94 |
| R22 | a capability mapping is a translation and needs an independent witness -- the caption; a named host resource is not necessarily a command; refusal must be visible | 18 mapped + 3 named separators = 21 of 21; caption guard caught `tools.data_browser` on "Class Browser"; Tk provides 7 of 18 and refuses 11 by name |
| R23 | `FLOW` is the container's field, not the child's -- `row` and `column` were unreachable, not untested; an unspecified `grid` is refused, not stacked; a derived position is declared | A/B render of one authored document with zero coordinates; 228 groups reproduced at 15.8%, corrected to 214 visual groups at 12.1%; 9 of 21 `row` groups were DataEnvironments |
| R24 | a document's requirements are computable from the table alone, so refusal need not wait for a window; a reference is not a measurement -- `FONTREF` must resolve the object's own declaration | manifest and render agree on every refusal across 6 documents; 1688 of 3010 corpus objects declare a font, 98.9% resolve into their file's own cache; per-object `FONTREF` 0% -> 70.4%; `pageset` refused by the reference consumer until found |
| R25 | a bound control's width follows its MASK, not its field, and the schema determines the mask; a load-bearing property must be named, not passed through | 17 bound controls: R17 mean |err| 3.4 px, R25 1.1 px and exact on 11; ACCOUNTS 0.1 px on 8 of 8; 649 PROPS keys of which 1 is named |
| R26 | where a relation exists, the lock domain is the transitive closure of related work areas; locking only what you name is not serialization | correct per-workspace locking wrong 100/100, same as no lock; a trusting child handler returned another student's rows 100/100 |
| R27 | tab order is a second ordinal over the same children, not an attribute of one -- OWNER'S DECISION; duplicates refused to produce, tolerated to consume | 1445 of 2186 corpus objects carry one; 9 of 170 files hold a genuine duplicate; `crmfiles.scx` O002 is ORDINAL 1 and TABORDINAL 5 |
| R28 | a document's shape is specified and its contents are not; structure must not travel in a channel a reader may discard; an object whose children are only dotted property names is incomplete | independent implementer, contract only: 4 of 5 tables rendered, 1 correctly refused; 13 menu PROPS keys against section 11's 6; `UIDEF_STUDENTS` panel O020 loses 10 buttons silently |
| R29 | an object whose children are dotted property names is a COMPOSITE control, not a malformed one; a table that cannot express composition loses a quarter of the objects | 775 implied children lost across 170 files, 0.35 per imported object, 65% of files; 59 lost `page` objects and 81 group buttons |

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
- ~~**A hand-authored `.SCX` with real method code.**~~ **Closed 2026-08-19 by
  R14**, which found 169 of them in the corpus and answered the question they were
  wanted for. Note the specimens are still all designer output locally; the
  corpus supplied the hand-authored code, and `.VCX` method bodies remain
  unmeasured. Original entry follows.
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
