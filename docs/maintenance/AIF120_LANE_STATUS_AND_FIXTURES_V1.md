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
| Rulings **R13 through R75** live in their own files; this ledger is their only index. The charter does not carry them. | -- |
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
| **R30** -- the composition rule, implemented: 138 members materialised, 0 count mismatches; corrects R29 | `docs/maintenance/AIF120_COMPOSITION_RULE_V1.md` |
| **R31** -- `.VCX` read as a class library; instances flattened, `PROVENANCE` gains `inherited` | `docs/maintenance/AIF120_CLASS_RESOLUTION_V1.md` |
| **R32** -- handlers inherit; nine standard events restored, `Unload` chief among them -- OWNER'S DECISION | `docs/maintenance/AIF120_METHOD_INHERITANCE_V1.md` |
| **R33** -- codepage honoured; binary columns unpacked; the DSL bypasses x64base's own locale catalog | `docs/maintenance/AIF120_LOCALE_AND_ENCODING_V1.md` |
| **R34** -- a second backend on a different geometry model; the refusal set is a property of the target | `docs/maintenance/AIF120_SECOND_BACKEND_V1.md` |
| **R35** -- a character-cell backend: band before quantising; `ignored` is a missing conformance outcome | `docs/maintenance/AIF120_CHARACTER_CELL_V1.md` |
| **R36** -- `SOURCE` carries relations; the manifest computes the lock domain. R26.2 closed | `docs/maintenance/AIF120_RELATION_SOURCE_V1.md` |
| **R37** -- a backend-independent runtime that takes the lock the document names | `docs/maintenance/AIF120_RUNTIME_V1.md` |
| **R38** -- the Tk backend adopts the runtime; the chain runs end to end | `docs/maintenance/AIF120_RUNTIME_ADOPTION_V1.md` |
| **R39** -- one scope per container; concurrency is declared, not configured | `docs/maintenance/AIF120_CONTAINER_SCOPE_V1.md` |
| **R40** -- a compiled wx C++ backend; compiling is not rendering | `docs/maintenance/AIF120_WX_BACKEND_V1.md` |
| **R41** -- the dispatch runtime in C++; the rule survived the primitives | `docs/maintenance/AIF120_WX_DISPATCH_V1.md` |
| **R42** -- a ruling shipped and its code did not; `git add` on an ignored path is a silent no-op | `docs/maintenance/AIF120_SHIPPED_RULING_UNSHIPPED_CODE_V1.md` |
| **R43** -- the citation check earns its place in the gate; a line may opt out, and the opt-out is greppable | `docs/maintenance/AIF120_CITATION_GATE_V1.md` |
| **R44** -- the wx backend shipped R39's one-scope-per-window defect; container scopes, with a control run | `docs/maintenance/AIF120_CONTAINER_SCOPE_WX_V1.md` |
| **R45** -- nested cancellation on both targets; destroying a group segfaulted, and the safe fix stopped cancelling descendants | `docs/maintenance/AIF120_NESTED_CANCELLATION_V1.md` |
| **R46** -- a notebook owns its pages; the third removal verb, and the first case where the rule must NOT fire | `docs/maintenance/AIF120_PAGE_TEARDOWN_V1.md` |
| **R47** -- the runtime was not using x64base's locks; FLOCK() refuses rather than queues, and the deadlock was in the reimplementation | `docs/maintenance/AIF120_LOCK_SEMANTICS_V1.md` |
| **R48** -- record granularity via the house's bare `LOCK`, which carries no number and so has no AIF-116 surface | `docs/maintenance/AIF120_LOCK_GRANULARITY_V1.md` |
| **R49** -- the lock verbs move into the runtime on both targets; the C++ seam let a target reintroduce AIF-116 | `docs/maintenance/AIF120_PROVIDER_PARITY_V1.md` |
| **R50** -- cross-process locking proven against the real binary; the release verb was unlocking the record, not the table | `docs/maintenance/AIF120_CROSSPROCESS_LOCK_V1.md` |
| **R51** -- crash reclaim holds both ways; the Windows liveness branch reads access-denied as dead (reported to AIF-116) | `docs/maintenance/AIF120_LOCK_RECLAIM_V1.md` |
| **R52** -- record granularity and the rollback proven; a table lock does not exclude a record lock, correcting R48.3 | `docs/maintenance/AIF120_RECORD_AND_DOMAIN_V1.md` |
| **R53** -- `BINDING` gets a syntax measured from the corpus, and `SOURCE`'s work areas get an owner | `docs/maintenance/AIF120_BINDING_SYNTAX_V1.md` |
| **R54** -- table and record locks are independent by owner ruling; R52.1 withdrawn, and the owner token carries no account | `docs/maintenance/AIF120_LOCK_INDEPENDENCE_V1.md` |
| **R55** -- the house already had a GUI threading contract; detached workers fixed, two conflicts reported | `docs/maintenance/AIF120_HOUSE_GUI_CONTRACT_V1.md` |
| **R56** -- the `FONT` row carries emphasis; gate 11's fix 1, and a cache field that looks like a style flag is not one | `docs/maintenance/AIF120_FONT_EMPHASIS_V1.md` |
| **R57** -- typed lock provider with no toolkit dependency; a handler's record lock does not survive its own write | `docs/maintenance/AIF120_TYPED_PROVIDER_V1.md` |
| **R58** -- a generated wx frontend drives the real engine end to end; R53.4 implemented | `docs/maintenance/AIF120_END_TO_END_V1.md` |
| **R59** -- R26's relation closure acquired through the engine; a write keeps the table lock that allowed it | `docs/maintenance/AIF120_DOMAIN_END_TO_END_V1.md` |
| **R60** -- two typed frontends contend and the rollback path executes; the witness had to come from inside the sequence | `docs/maintenance/AIF120_CONTENTION_V1.md` |
| **R61** -- `open()` is not `USE`; the engine has two typed layers, and `uidef.py`'s tables are engine-readable | `docs/maintenance/AIF120_ENGINE_SURFACE_V1.md` |
| **R62** -- x64base is not FoxPro; `SET REPROCESS` withdrawn, and the SQL surface is a limit the contract does not state | `docs/maintenance/AIF120_NOT_FOXPRO_V1.md` |
| **R63** -- the lock path holds past 2^31; `recno()` would have written `.lock.-1` for every record | `docs/maintenance/AIF120_LOCK_BOUNDARY_V1.md` |
| **R64** -- the house already had a proof language; the lane's lock contract restated in `.dts`, and `UNLOCK` reports a success it never measured | `docs/maintenance/AIF120_DOTSCRIPT_V1.md` |
| **R65** -- the grid already ships and the design table cannot describe it; `BINDING` is a subset of the engine's spec grammar and `#n` is deleted by the lexer | `docs/maintenance/AIF120_TUPLE_SPEC_V1.md` |
| **R66** -- five frame kinds measured from `ERSATZ` with read-only written in; the lock provider confirms instead of believing | `docs/maintenance/AIF120_FRAME_KINDS_V1.md` |
| **R67** -- the grid imports from the corpus, 17 of 17 obey the Relation rule, and `TupleStream` is the kind's runtime contract | `docs/maintenance/AIF120_GRID_IMPORT_V1.md` |
| **R68** -- the trinity's six rules, and what an x32 fallback costs; RECNO64 completion gate 3 is open at the tuple stream | `docs/maintenance/AIF120_X64_FALLBACK_V1.md` |
| **R69** -- the tuple stream widened to RECNO64; it could not position past 2^31 and the CDX order vector truncated 64-bit recnos to 0 | `docs/maintenance/AIF120_TUPLE_STREAM_RECNO64_V1.md` |
| **R70** -- the generated grid binds `DbTupleStream`; running it found a relation the document declared and the runtime never made, and a star spec that dropped every field after the first | `docs/maintenance/AIF120_GRID_STREAM_BINDING_V1.md` |
| **R71** -- UIDEF promoted from lane to `project.x64base.gui`; the registry already said where a non-C++ product goes, and the move is a promotion under AIF-040 rather than a tidy-up | `docs/maintenance/AIF120_PROJECT_PROMOTION_V1.md` |
| **R72** -- the host contract was already written inside `run_shell()`; R70.5's relation setup relocated from generated code into the host lifecycle, and the cursor hook that already answers selection-follows-record | `docs/maintenance/AIF120_HOST_CONTRACT_V1.md` |
| **R73** -- `Order` named an index FORMAT the document does not choose, and could name one the table does not have; two modes, not three | `docs/maintenance/AIF120_ORDER_VOCABULARY_V1.md` |
| **R74** -- the `tree` and `summary` rendered placeholders next to an API commented `Debug / UI`; and the second grid shape the engine has and UIDEF cannot express | `docs/maintenance/AIF120_RELATION_FRAMES_V1.md` |
| **R75** -- the sixteen refusal fixtures every measurement is quoted against existed only in the session container, and the citation gate could not see it | `docs/maintenance/AIF120_FIXTURE_CORPUS_V1.md` |
| **White paper** -- lane congruence: how a frontend lane found engine defects behind a gate the engine lane had already declared | `labtalk/ai_portal/whitepapers/WHITE_PAPER_LANE_CONGRUENCE_V1.md` |
| The UIDEF tooling | `gui/uidef/uidef.py`, `import_scx.py`, `import_mnx.py`, `uidef_tk.py`, `uidef_tk_menu.py`, `author_uidef.py`, `dispatch_test.py`, `infer_flow.py`, `contend_test.py`, `lifetime_test.py`, `uidef_tk_host.py`, `author_flow.py`, `manifest.py`, `author_fonts.py`, `author_tabs.py`, `relate_test.py`, `classlib.py`, `uidef_html.py`, `uidef_text.py`, `uidef_runtime.py`, `locked_test.py`, `adopt_test.py`, `scope_test.py`, `uidef_wx.py`, `uidef_rt.h`, `wx_demo_registry.cpp`, `cite_check.py`, `shell_session.py`, `wx_host.cpp`, `author_cases.py` |
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
| R30 | a composite control's members materialise as ordinary rows -- the table could always express composition, the importer never did it; inheritance is a separate and larger question | 918 dotted prefixes: 646 inherited from a `.VCX` (118 parents), 272 inline (72 parents); `buttoncount`/`pagecount` give a checkable member count; CLASSLOC 412 relative / 0 absolute in the corpus, absolute in our own fixtures |
| R31 | a `.VCX` is a sequence of class blocks delimited by a declared record count; a class is identified by block and liveness, never by name; an instance is flattened and says so | 25 libraries, 110 live classes, 0 count mismatches; 3 blocks named `frmsolution`, 2 deleted; 31% of VCX records deleted against 0% of SCX/MNX/FRX; 351 of 431 references resolved, 363 members materialised |
| R32 | a handler reference defined on a class reaches the instance; an event the instance defines itself wins -- OWNER'S DECISION | 788 handlers inherited, rows with HANDLERS 1047; section 9 was missing 9 standard events over 92 handlers, `Unload` 72 of them while `Load` was carried |
| R33 | a table must honour the codepage it declares, and binary columns are not text; the design table embeds literal captions while x64base ships 4756 texts in 5 locales behind SET LOCALE | round trip proven in cp1250/1252/1253/932/1256; 79 binary columns were decoded as text; text-field decode failures 15 -> 1; R30/R31 figures unchanged |
| R34 | `FLOW`, `SPAN` and `TABORDINAL` are the target's own concepts, not Tk conveniences; refusal is a property of the target, not the format | one coordinate-free document rendered by place/pack/grid and by flexbox/CSS grid, both refusing the same two rows for the same reasons; tk refuses 12 capabilities where html refuses 11 |
| R35 | a coarse target must BAND coordinates before quantising, which is R19's inference finding governing rendering; `ignored` is a conformance outcome the contract cannot express; `ORIGIN_SCALE=cell` is unexercised and unconvertible | three backends return the identical verdict on a coordinate-free document; 19 TOP values banded into 10 visual rows; 20 of 20 corpus ScaleMode declarations say pixels |
| R36 | a document states its own lock domain: `SOURCE` gains `Relation`, and the closure is computed from the table before any window exists | 8 relation records the importer had been discarding; a three-edge chain resolving to one domain of four work areas; first real document to hit R27's partial-tab-order case |
| R37 | the concurrency rules hold in the runtime a generated frontend embeds, not only in a model; the lock domain is read from the document, not configured | 60/60 wrong locking the named work area, 0/60 locking the relation set, one constructor argument apart; cancel, failed, no-completion and no-capability all refused or dropped correctly |
| R38 | a runtime, a profile or a rule is `planned` until a consumer uses it -- writing it and writing about it are the same tier | two handlers naming DIFFERENT work areas serialized against each other because the document declared a relation; `TotalGpa` leaves before `ListEnrolments` enters, on threads neither handler chose |
| R39 | a generated frontend's concurrency is DECLARED, not configured: two handlers run at once if and only if the document does not relate the work areas they touch | destroying one panel dropped only its own completion while the sibling's work finished; two unrelated areas ran concurrently where R38's related pair serialized |
| R40 | for a compiled target "it builds" is a syntax check, not a proof -- the evidence is still the render; a target may clip its own container decoration, which R16 does not cover | five tables generate wx C++ and g++ builds all five; `SPAN` reaches a third independent spelling in `wxGBSpan`; the first version compiled cleanly and rendered every group empty |
| R41 | `DISPATCH` and the lock domain are properties of the DOCUMENT, not of a runtime -- two implementations sharing no code and no language produced the same orderings from the same table | R38's Python timeline reproduced on `std::thread`/`std::mutex`/`CallAfter`: serialized on the relation set, overlapped on per-area locking, one runtime argument apart |
| R42 | a green gate is evidence about what was STAGED, not what was intended; `git add` on a gitignored path is a silent no-op | R33's fix was absent from the tracked reader for two hours; nine committed tools would not import on a fresh clone; R30's document was a widow cited by three rulings |
| R75 | a gate sees the shape it was built to see -- `cited-paths` makes untracked POINTERS visible and leaves untracked EVIDENCE invisible whenever the evidence is cited the way a person cites it | eighteen UIDEF documents carry every measurement in R66, R70, R73 and R74; four regenerate from tracked author scripts and **the other sixteen -- the N*/P* negative and property cases, the ones that prove the gates actually refuse things -- were built ad hoc during R66 and R70 and existed ONLY in the session container**, so a reader with a clone could read "6 of 18 refused" and reproduce none of it; nine rulings went by without the gate noticing, because the rulings cite them by BARE NAME (`N1_editable_grid`, `P4_rowlimit_big`) and `PATH_RE` matches paths -- a gate silent about a class of thing is not evidence the class is clean; `author_cases.py` reproduces all sixteen, verified BEHAVIOURALLY (identical `stream_refusals` and identical generated C++, 16 of 16) rather than by byte, because regeneration legitimately moves three bytes -- one DBF header date stamp and two memo BLOCK POINTERS, which are positions in the .FPT and not content; the binaries stay untracked because they are derived, which is why FRAMEDEMO.DBF was never tracked either and that part was always right |
| R73 | a vocabulary that names an IMPLEMENTATION rather than a MEANING will eventually let a document ask for something that cannot exist | contract 4c closed `Order` to `physical|inx|cnx`, one word per setter -- and `set_order_inx()` (db_tuple_stream.cpp:547) and `set_order_cnx()` (:553) are BYTE-IDENTICAL, both setting `NavMode::OrderVector` and neither attaching an index or selecting a tag, confirmed at runtime where all three spellings returned identical pages; `WORKSPACE OPEN` says "indexes are chosen by DBF flavor" and the MCC schema across four flavors proves it -- og `v32` CNX+INX, vfp `vfp`/runtime `v64` CNX+INX, x32 `v32` CNX+INX, x64 `v64` **CDX+CNX** -- so **`INX` does not exist for x64** and 4c called `Order = inx` legal there; which index and which tag are WORKSPACE facts, already carried per area by a `DTSHEMA 2` row as `index=`/`indextype=`/`tag=`; and the defect I shipped into R70 is that `set_order_*` returns void while `WORKSPACE OPEN` can report `[index: STUDENTS.cdx, found (not attached)]`, so a bound grid asks for an order, is told nothing, and browses physical in silence |
| R74 | a placeholder is a question you did not ask -- and a defect fixed at one site instead of turned into a rule is a defect scheduled to recur | `summary` rendered `ENROLL : n` with a LITERAL n and `tree` drew SOURCE edges with no counts, while `set_relations.hpp` had `match_count_for_child()` and `list_tree_for_current_parent()` sitting under a comment that reads `// Debug / UI`; now filled, measured live at `ENROLL : 2` and `-> ENROLL ON SID  (matches: 2)`; the maintainer's REL ENUM demo also showed the engine has a SECOND grid shape -- `enum_emit_for_current_parent(path, max_rows, emit)` enumerates a declared PATH across five aliases where 10c describes only a SPEC over the current record -- recorded and deliberately NOT designed, because a half-specified `Path` property would be R6's generate-from-a-count mistake in a new place; and correction 54: R70.3's unused-helper fix was applied to one helper and not generalised, so two new helpers reintroduced it on six of eighteen fixtures immediately |
| R72 | the host you are about to design is usually already written somewhere with a loop wrapped around it -- and a seam is invisible to a search shaped like a feature | `run_shell()` (src/cli/shell.cpp) is three parts and a GUI replaces ONE: host setup at 506-550, the stdin REPL at 551-769, teardown at 770-789 REVERSED, every acquisition released -- and the terminal-specific portion is three lines (`isatty`, `applyTheme`, the banner); `src/tv/foxtalk_app.cpp:469` and `cmd_foxpro.cpp:568` were ALREADY hosting this engine from a non-CLI frontend through the same `shell_engine()` seam, both passing `include_ui_cmds=false`, which is R11's discovery-after-declaring-absent repeated for the same reason; **R70.5 was right about the defect and wrong about the address** -- three of its four emitted lines are `shell.cpp:532-534` verbatim, so the generator was re-implementing house initialization once per document inside `OnInit` with no teardown, now split so the DOCUMENT owns what (`uidef_attach_source`) and the HOST owns when; I had also written that "nothing connects grid selection to the current record" while `cursor_hook::set_callback` + `on_cursor_changed` (shell.cpp:339) is exactly that signal, an absence asserted from the shape of my own question; the command surface is CATALOGED with a written contract saying a GUI may label and invoke but never redefine, ALIASES load with `register_shell_commands` (shell_commands.cpp:314/517/549) and SHORTCUTS are a separate mechanism rewriting the leading token first (`expand_shortcut_lead`, shell.cpp:682), and that surface costs **+272 translation units measured by nm -- 46 for a grid, 318 with commands**, which is R61's boundary with a number on it; and correction 53: adding an `OnExit` override split `return true; } };` for EVERY document, so the byte-identical-without-`--stream` invariant failed on a purely cosmetic change, which is why that invariant is a real gate |
| R71 | where a thing lives is a doctrine question the tree usually already answers -- and a migration's real bill is the prose nobody executes | AIF-040 promotes a lane that "spawns sub-lanes, gains an independent lifecycle, or becomes a program others build under", and AIF-120 met all three before the question was asked; `projects.yaml` roots FOUR non-C++ products inside ccode -- `pycrud`, `dottalk-webui`, `sqlite-gui` (`kind: gui_project`) and `bindings/pydottalk` -- and roots ZERO outside it, so "ccode implies C++" is a fair reading of the name and not a description of the tree; the premise "it's not C++ code" measured 13 `.cpp` and 2 `.h` out of 53 files, a quarter, which is why a Python-product home under `bindings/` would have been wrong too; NOTHING executable references `gui/uidef` -- not CMake, not the gates, not the registries -- so the entire cost is 251 citations in 54 documents PLUS 31 self-references inside the tooling's own usage strings and build comments, which I missed on the first pass and printed "empty means the move cannot break the tools" directly above the thirty-one lines that said otherwise; and the move and the citation rewrite must be ONE commit or the citation gate sees 55 widows in between |
| R70 | a rule that is CHECKED on a declaration proves only the declaration -- the reader has to act on it, and the way you find out whether it did is to RUN the thing, not compile it | the generated wx window built, linked 44 house translation units and rendered three students against ONE enrollment, because the document declared `STUDENTS -> ENROLL ON SID`, the manifest checked it, the `tree` drew it, and nothing ever told the ENGINE about it -- no error anywhere in the path; a `*` or `alias.*` spec is ONE spec and N values, so the generator set items on columns that did not exist and dropped every field after the first, fixed by taking arity AND labels from `TupleRow::columns` because the engine is the only thing that knows them; `-fsyntax-only` cannot see `-Wunused-function` at all, so every check here is `-c`; the refusal set is the manifest's own (`stream_refusals`), which catches 6 of 18 fixtures including R6's editable grid and R65.3's ordinal spec; and after the fix the three rows match `DOTSCRIPT aif120/r70_stream.dts` character for character, which is the first time a generated frontend and the house shell have answered the same question the same way |
| R69 | a narrow type is not always dead weight -- sometimes it is LOAD-BEARING, and widening it is how you find out; and a build configuration you did not check the state of is not a build you verified | `safe_rec_count` read `recCount()`, the accessor that returns **-1** past INT32_MAX BY DESIGN, so every bound check became `r > -1` and the Smart Browser and every tuple cursor were INERT on exactly the tables RECNO64 exists to serve; `collect_lmdb_cdx_recnos` read full 64-bit recnos out of the x64 CDX/LMDB index and stored them in `uint32_t`, where 2^32 truncates to **0** -- the engine's own "no current record"; the order vector is PURE 64 by owner ruling, so truncation is impossible rather than refused, while 32-bit FORMATS still load through their own width and widen on the way in; and I reported eleven translation units clean while `#if DOTTALK_WITH_INDEX` was OFF in my container -- the excluded block was the one containing the defect, and MSVC found it in three lines; and REGRESSION ALL is green with INDEX_X64's ordered output BYTE-IDENTICAL to the pre-change baseline, which is what a widening should look like and what a truncation would not |
| R68 | an x32 fallback is a CAPABILITY REPORT, not a narrow code path -- the trinity stores resolved truth in the widest type and lets narrowness exist only at an accessor, and the house's own five words for it are "one engine API, three capacities" | six rules read out of `xbase.hpp`/`xbase_vfp.hpp`/`xbase_64.hpp`: the fallback is a LAYER not an `#ifdef`, the core has no 32-bit storage at all, the narrow accessor SIGNALS (-1) inward while an outward mirror SATURATES and carries an agreement predicate, the narrow entry point is an ADAPTER (`gotoRec(int32_t) -> gotoRec64`) so the path never forks, and fallback covers names and metadata but never structure; `long` is the tell -- the trinity never uses it and `db_tuple_stream.hpp` has 13, which is why that file is 64-bit on the WSL build and 32-bit under MSVC; and RECNO64's own completion gate "Relations/tuples preserve them" is open in exactly the consumer its plan named |
| R67 | a rule argued from one authored document is an argument; the corpus decides it -- and the RUNTIME half of a kind may already exist in the engine, written before the vocabulary that names it | 33 corpus grids: 99 `alias.field` column bindings and 0 bare, 17 producing a tuple spec, **17 of 17 satisfying 10c's Relation rule**, and **0 of 33 declaring `ReadOnly = .F.`** so 4b(b) costs nothing; four distinct import refusals proven on real forms (computed expression, `ColumnCount = -1` which is R6's original case by name, `RecordSourceType 4`, no ControlSource); `src/cli/tuple_stream.hpp` turned out to BE the grid's contract -- `next_page(max_rows)` is `RowLimit`, `status_line()` is the statusbar, `set_order_*` closes `Order` to three values -- and a REPL like `SMARTBROWSER` is bound as a peer over the stream, not called as a command; and the stream is 32-bit (`int32_t` cursor snapshot, `long` under MSVC, `uint32_t` order vector) where R63 proved the engine is 64-bit |
| R66 | a constraint has to be written into a kind at the moment the kind is added, or documents get authored against the permissive reading first -- and a rule that answers an old objection (R6) should say so rather than quietly dropping the entry | the vocabulary goes 14 -> 19 with `grid`, `tree`, `detail`, `summary`, `statusbar`, and `ReadOnly` false is REFUSED naming BETA-7.1; `grid`'s columns come from BINDING so R6's implicit-children objection does not reach it; four targets render the frame (wx clean under `-Wall -Wextra`, six Tk widgets all mapped) and eight bad documents refuse with distinct reasons; `manifest.py` had been keeping only the LAST alias of a multi-area SOURCE because `parse_props` returns a dict, so the `not declared in SOURCE` check could not fire; and the lock provider now CONFIRMS every acquire and release against `LOCK STATUS` -- which catches correction 34's wrong release verb on the first run, a defect that previously cost three rulings |
| R65 | the charter is to give a language to the GUI THAT EXISTS -- the design table was measured against VFP `.SCX` forms and never against the browses this house ships, so it cannot name a single region of the one screen the engine renders by itself | `ERSATZ GRID` is a five-region frame (root detail, relation tree with join conditions, descendant counts, a tuple grid whose columns SPAN two work areas, a rows-shown/limit/status footer) and `KIND` has a word for none of them; `BINDING`'s `alias.field` is a strict subset of BETA-4.4's `*, AREA.*, AREA.FIELD, #n`, and `TUPLE --AREA-PREFIX` prints R53's exact syntax as OUTPUT; `#n` never reaches the spec parser because AIF-037 cuts `#` to end of line, so `TUPLE #1` prints ten fields and looks like it worked; and `ERSATZ GRID` renders three of its five regions blind while `ERSATZ REFRESH` renders the same state complete |
| R64 | prior art was being checked for LIBRARIES and DOCUMENTS and not for METHOD -- the house ships `.dts`, a REGRESSION catalog, a self-asserting proof form and the doctrine that every test sets its own environment, and seventeen rulings built a parallel apparatus beside it | the lane's lock contract runs green as one `.dts` regression: `LOCK TABLE` leaves the record unlocked and `UNLOCK` leaves the TABLE locked (correction 34 and R54 on one screen); `UNLOCK 77` prints "record 77 unlocked" while `LOCK WHO 77` says "no lock recorded" -- `cmd_unlock.cpp` calls the void best-effort overload at all three sites while `xbase_locks.hpp` ships a `bool`+`err` one; `LOCK STATUS` reports the CURRENT record, not the locked one; and `WORKSPACE LOAD` resolves `.DBF` against `.dbf` so `REGRESSION NONDESTRUCTIVE` cannot reach sections 07-15 on POSIX (the house's own BETA-1.2) |
| R63 | a lesson written down is a RECORD, not a guard -- correction 38 was documented four rulings ago and reproduced verbatim here; and a fixture must be built with the API the house already ships, not with header bytes I decode myself | `recCount64()` reads 2147483649 and `recCount()` returns -1; `try_lock_record(recno64())` writes `.lock.2147483648` while `recno()` would have written `.lock.-1` for EVERY record past 2^31, all colliding -- the wrong accessor is visible on disk rather than silent; fixture built with `create_dbf(..., Flavor::X64, ...)` at 8.0K allocated, 19G logical |
| R62 | VFP is the source of the DOCUMENT FORMATS and nothing else -- reading `.SCX`/`.VCX`/`ControlSource`/`FontBold` is the charter, but runtime vocabulary was imported with it and x64base is only SIMILAR to FoxPro, with a SQL-ish flavour | `FLOCK` occurs once, inside a regression DESCRIPTION STRING; `rlocked` is a local bool; `SET REPROCESS` does not exist, so the open item R47 and R48 both carried is withdrawn -- while the measured behaviour (a busy domain refuses) is untouched, since only its NAME was borrowed; and SQLSEL/WHERE/ORDER BY/LIMIT exist while `SOURCE` and `BINDING` can only name work areas |
| R61 | the primitives are in the libraries and the COMPLEX COMMANDS are at the dottalkpp level, by design -- so a frontend links `xbase::locks` AND embeds the command layer via `shell_execute_line`, and neither is console parsing; `open()` is a file open, `USE` is the operation that attaches memo and index, guards duplicates and resolves paths | measured with `nm`: no `cmd_USE`, `cmd_COMMIT` or `shell_execute_line` in any archive; three `uidef.py`-written tables open cleanly in the engine (0x30, 16 fields, correct counts), which nothing had ever checked; R58's "R53.4 implemented" corrected -- it implemented the refusal half, not the opening half |
| R60 | a harness for an ASYNCHRONOUS property fails in the same shapes the property does, so no sampler can settle it -- the acquire-fail-release window is microseconds and a 1ms timer cannot see it; the witness must come from INSIDE the sequence (the resolver, which the provider must call to act) | two processes: the contender takes `enroll`, is refused `students` by the engine, returns `enroll`, and the handler never runs (`refused (domain busy)`); attempt 2 passed while testing nothing because a 3s hold expired against a 3s sleep and the handler simply RAN |
| R59 | a rule argued in July executed in August against the system it was written about -- R26's closure was measured in a MODEL (60/60 corrupt when locking the named area) and is now observed locking two real DbAreas from a frontend generated out of a document | a handler fired on `students` holds students AND enroll; the second, fired on `enroll`, WRITES to `students` -- an area it never names -- which is the hazard R26 exists to cover, and its table lock survives the write exactly as R57.2 predicted from the record case |
| R58 | a top-down design that has to SIMULATE the system beneath it has not met it -- the typed provider is 60 lines with no adapter, no translation layer and no emulation of engine behaviour, which is the positive form of R47's correction; and a warning nobody enables is a warning nobody has | the full chain runs in one process: UIDEF table to generated wx to uidef::Runtime to xbase::locks to DbArea, reading recCount64=200 with the table lock held by the ENGINE during the handler; fourteen wx builds since R40 never passed -Wall, which was hiding a capture-of-global warning in every generated file |
| R57 | a harness reporting on someone else's code is itself UNTESTED CODE, and its failures wear the costume of the thing it measures -- fourth time this run (R44.4, R45.6, R49.4, and an unsequenced printf argument that framed the engine for the probe's own bug); and a dependency added for a NAME cost the header its testability everywhere but one machine | linked against the real libxbase: a handler's record lock is deleted by DbArea's own write path, because same-owner re-entrancy returns true without a depth count and the innermost unlock wins; the table lock survives the same write, so R48.3's default now has a MEASURED reason after R54 withdrew its original one |
| R56 | a tidy pattern over three data points is not a rule -- the font cache's field 2 takes 0/1/2/3/4/32/128 with `3` exactly where `bold|italic` would fall, and correlating it against declared bold agrees 33 times and disagrees 85; the corpus is what stopped it reaching the contract | 161 corpus objects declared an emphasis the table dropped (158 bold, 3 italic); a font's identity is now name+size+bold+italic on all three font-bearing backends, with Tk read back from `font actual` rather than from the generator's intent |
| R55 | the fourth prior-art miss and the largest -- a lane chartered to "give the existing GUI a language" built a dispatch runtime, a second one in C++, scopes and a CLI bridge across nineteen rulings without opening `docs/ui/`, where the house GUI threading and RAII contract already specified all of it; and REPORT a rule that blocks rather than complying silently | both runtimes ran the contract's named anti-pattern (`daemon=True` / `.detach()`), now owned and joined with every harness reproducing; two derivations agreeing is evidence about the RULES and no excuse for the duplication; "one workspace/session has one mutation lane" contradicts R26's measured domain concurrency, so one of two documents is wrong today |
| R54 | ALWAYS LOOK FOR PRIOR ART -- the house rule, named by the maintainer after the third time in one run that he applied it and the author did not (R33 locale, R47 locking, R54 identity); evidence of a thing working is not evidence the thing should exist, and this lane's rigour made each wrong artifact MORE convincing | R52.1's "defect" was the intended semantic and is withdrawn, taking its AIF-116 finding with it; the owner token is `host:pid:ms` with no account and no session while AIF-045's identity layer sits unused; `bbs_server.cpp` serves every session from one process-global identity, so one session can unlock another's record |
| R53 | when the implementation is the specification, the rule is whatever the code happens to do -- `manifest.py` enforced `alias.field` from the day it was written and the contract never said it; and a refusal must name the RIGHT reason, since "not alias.field" tells an author they made a typo about a feature they used correctly | 170 forms, 159 ControlSource occurrences: 145 alias.field, 8 empty, 4 object references, 2 bare field; the 4 object references were skipped in SILENCE past a comment claiming they were already refused; the lock provider's `SELECT <alias>` presumed a `USE` no ruling had ever assigned |
| R52 | "conservative" is a claim about WHAT it excludes, and coarser does not automatically subsume finer -- `LOCK TABLE` succeeds while another process holds a record, so R48.3's conservative default was conservative against table lockers only; and a test whose subject may not have happened needs a witness that it did (C0) | bare LOCK refuses record 1 and grants record 5, so the granularity is genuine; the rollback releases the first area with the roller-back still ALIVE; a harness bug uncovered that the provider's `SELECT <alias>` presumes a `USE` nobody in the runtime or contract issues |
| R51 | two requirements that pull against each other must be tested in the order where the cheap wrong answer fails FIRST -- a check that always reclaims passes "dead owner reclaimed" on its own; and reading the source to explain a PASSING test is where the next defect was found | SIGKILL between LOCK and UNLOCK is recovered from, and a live owner is refused; `is_pid_alive` handles POSIX EPERM as alive but its Windows branch reads access-denied as not-found, so a live cross-user lock can be declared stale; `ms=` is written to the sidecar and never read, so pid reuse makes a lock immortal |
| R50 | a proof must EXCLUDE the incidental mechanism -- three green steps proved nothing about release because process exit explains them equally well, and only keeping the holder alive can tell the two apart; and reading one side of a paired API and assuming symmetry cost three shipped rulings a leaked table lock | `LOCK: failed (lock exists)` against the shipped binary confirms R47's FLOCK ruling; `UNLOCK` was unlocking record 1 while `Table: LOCKED` still stood; owner strings came back ungrouped, independently confirming AIF-116's fix from outside its lane |
| R49 | a rule the runtime cannot ENFORCE on one of its targets is a rule that target does not have -- R48.2 held by construction in Python and was merely hoped for in C++, where the seam handed a target the aliases and let it write its own commands; and in an event-driven harness, decide what the output should look like BEFORE running it, because afterwards every shape has an explanation | the C++ provider now emits command text byte-identical to Python's under a global grouping locale proven live (`an un-imbued stream writes 16,984`); four cases pass on both targets; the AB-BA refusal count is interleaving-dependent, so only the invariants are asserted |
| R48 | the safest handling of a dangerous value is not to write it -- bare `LOCK` locks the current record and carries NO number, so AIF-116's surface is absent rather than handled; and finer is not safer, since a handler that SCANS an area needs all of it and the document cannot say which it does | `LOCK 16,984` round-trips as `16` in two lines of C++; the provider emits no digit outside `SELECT <alias>`; a refused second area rolls back the first, because a lock held by a process that does not think it holds one is never called stale |
| R47 | ASK WHETHER THE HOUSE ALREADY HAS IT -- a locking model was built, proven and reasoned about for ten rulings beside `xbase::locks`, which was there the whole time; and a guard is a claim that what it guards against is possible, so try-semantics DELETED the deadlock guard rather than keeping it | `try_lock_table` never waits, so the AB-BA hang reproduced in 4s cannot form; a busy domain now refuses (`complete Done refused`) on Python and C++ alike; R26 re-measured -- area 40 started / 0 refused / 60-of-60 wrong, domain 40 started / 20 refused / 0 wrong |
| R46 | detaching is not destroying -- the first test in the lane whose correct result is that NOTHING is cancelled, which every prior scope test would have passed while cancelling too eagerly; and a helper that covers most container kinds is invisible at the call site for the rest | destroying a notebook page segfaulted (exit 139) one commit after R45 named it untested; RemovePage/forget leave the work running on both targets; destroy_container now covers five container kinds by enumerating three owners |
| R45 | a lifetime rule must not depend on WHICH API ended the lifetime -- two ways of removing the same container disagreed about R21.4, and the one that crashed had the semantics right; naming a thing is a promise you can use it | destroying a group segfaulted (exit 139) because a wxStaticBoxSizer owns its box; the safe teardown then completed a destroyed container's descendant; three destruction targets now match cell for cell on wx and Tk |
| R44 | a fix applied to one backend does not travel to a backend written from the version BEFORE it -- R40/R41 were written from R38 and inherited the defect R39 had already named; and a harness for an asynchronous rule can fail identically to the rule being broken, so it ships with its control | the R38 shape drops BOTH panels' completions on one panel's destruction, the R44 shape drops one and delivers the other, and Tk produces the identical log from the identical table |
| R43 | an advisory that fires correctly on every commit is an advisory nobody reads -- so suppress DOCUMENTATION of an untracked path and REPAIR dependence on one; and "it parses" is R40's syntax check wearing Python | 43 documents, 122 cited paths, 122 tracked, exit 0 -- the first moment every path the lane points at is a path the repository ships; both tools shipped with `cited()` returning `None` and parsed fine |

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
