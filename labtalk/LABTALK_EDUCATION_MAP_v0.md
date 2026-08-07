# LabTalk Education Map v0

Status: draft campus map
Scope: LabTalk educational planning over DotTalk++ runtime evidence
Created: 2026-07-02

## Purpose

LabTalk is a living laboratory campus. This map connects CS101/CIS101-style learning
topics to the existing DotTalk++ educational reference, runtime commands, cases,
datasets, and proof gates.

The map is not a syllabus yet. It is a crosswalk from education intent to live
system evidence.

## Source Evidence

Primary sources:

- `include/edref.hpp`
- `src/edu/*`
- `src/cli/case_catalog.cpp`
- `docs/teaching/TEACHING_POINT_LEDGER.md`
- `docs/manuals/student/README.md`
- `docs/cases/REGISTRY_CASES_v0.csv`
- `dottalkpp/docs/cs101.txt`
- `dottalkpp/data/scripts/Your xBase_64 System as an Educational Platform.txt`
- `dottalkpp/docs/dottalkpp_legacy_doc_review_2026_05_09/LEGACY_REVIEW_MANIFEST.md`

Authority rule:

```text
Runtime behavior must be proven by current source, HELP/CMDHELP evidence,
case registry status, runtime smoke output, or explicit review. Curriculum
incubator documents are useful source material but are not runtime authority.
```

## Campus Model

```text
LabTalk Campus
  Course topic
    EDREF concept
      Runtime command or app
        Case or lab
          Dataset or artifact
            Proof state
              Student lesson
```

## Status Vocabulary

| Status | Meaning |
|---|---|
| `runtime_defined` | Source command or EDREF topic exists. |
| `case_registered` | Case exists in `docs/cases` registry. |
| `runtime_lab_candidate` | Case/lab is identified but still needs runtime proof attachment. |
| `curriculum_seed` | Teaching idea exists but needs promotion/review. |
| `incubator_source` | Legacy or generated curriculum source; mine only after review. |
| `student_ready_pending` | Strong candidate, but still needs student-facing review. |

## Education Crosswalk

| Course topic | EDREF topic | Runtime command/app | Case or lab | Evidence state | Next promotion step |
|---|---|---|---|---|---|
| Course orientation | `INTRO`, `EDUCATIONAL_USE` | `HELP`, `CMDHELP`, `CASE` | `HIST-090` DotTalk++ / LabTalk and the AI Future | `runtime_defined`, `case_registered` | Build first student path: open HELP, EDREF, CASE, then inspect one live table. |
| Systems model | `MODEL`, `STATE` | `STATUS`, `DBAREAS`, `WORKSPACE`, `BBOX` | `HIST-090`, `ENG-040` | `runtime_defined`, `runtime_lab_candidate` | Add a state-inspection lab showing work area, table, record pointer, order, filter, and metadata. |
| Sequential execution | `SEQUENTIAL`, `SCRIPT` | DotScript runner, command shell | `HIST-000` Data Trail Overview | `runtime_defined`, `case_registered` | Create a small `.dts` script that opens data, selects a table, sets order, and lists rows. |
| Decision flow | `DECISION`, `PREDICATE`, `EXPRESSION` | `IF`, predicate evaluator, expression functions | `ENG-020` SEEK vs SCAN | `runtime_defined`, `runtime_lab_candidate` | Attach examples showing conditionals over student data and predicate-driven selection. |
| Iteration | `LOOPS`, `SCAN` | `LOOP`, `WHILE`, `UNTIL`, `SCAN` | `ENG-020` SEEK vs SCAN | `runtime_defined`, `runtime_lab_candidate` | Contrast general loops with record-aware `SCAN`. |
| Tables, records, fields | `TABLE_RECORD_FIELD`, `SCHEMA` | `USE`, `FIELDS`, `STRUCT`, `DISPLAY`, `LIST` | `HIST-040`, `ENG-050` | `runtime_defined`, `runtime_lab_candidate` | Build a beginner lab around `STUDENTS.DBF` and `TEACHERS.DBF`. |
| Metadata | `METADATA`, `SCHEMA` | `DDICT`, `CMDHELP`, `CMDHELPCHK`, `METACOLLECT` | `ENG-040` Metadata and Data Dictionary | `case_registered`, `runtime_lab_candidate` | Crosswalk source contract, HELP DATA, data dictionary, and report-only validation. |
| Indexes and ordering | `INDEX`, `ORDER`, `NAVIGATION` | `SET INDEX`, `SET ORDER`, `CDX`, `IDX`, `SEEK`, `INDEXSEEK` | `ENG-010` Indexed Navigation | `runtime_defined`, `runtime_lab_candidate` | Prove CDX/LMDB/index path behavior with a student-visible navigation demo. |
| Search and matching | `SEARCH`, `FILTER`, `PREDICATE` | `SEEK`, `FIND`, `LOCATE`, `SET FILTER`, `WHERECACHE` | `ENG-020` SEEK vs SCAN | `runtime_defined`, `runtime_lab_candidate` | Show exact lookup, predicate scan, and filtered traversal. |
| Boolean logic | `PREDICATE`, `EXPRESSION` | `CALC`, `IF`, `WHERE`, `edu_boolean.cpp` | `ENG-020` | `runtime_defined` | Promote boolean examples from EDREF into student exercises. |
| ASCII and representation | `GLOSSARY`, expression topics | `ASCII`, `edu_ascii_table.cpp` | CS101 representation seed | `runtime_defined`, `curriculum_seed` | Add representation lesson: bytes, characters, field storage, and display. |
| Data projection | `TUPLE`, `PROJECTION` | `TUPLE`, `SMARTLIST`, `TUPEXPORT`, `REL ENUM` | `HIST-030`, `ENG-040` | `runtime_defined`, `case_registered` | Show how rows become projected information. |
| Relations | `RELATION`, `REL_ENUM`, `ENUM` | `SET RELATION`, `REL`, `REL ENUM` | `HIST-030` Unisys / CODASYL at ALCOA | `case_registered`, `student_ready_pending` | Tie CODASYL/network-database history to relation traversal and tuple projection. |
| Buffering and commit | `BUFFERING`, `COMMIT` | `BUFFER`, `COMMIT`, `ROLLBACK`, table buffer commands | `ENG-030` Buffering and COMMIT Lifecycle | `case_registered`, `runtime_lab_candidate` | Attach a safe reversible write lab with before/after proof. |
| Files and storage | `SCHEMA`, `METADATA`, `INDEX` | DBF/xDBF, CDX, LMDB, MEMO tools | `ENG-050` File-Based DB to Engine-Based DB | `case_registered`, `runtime_lab_candidate` | Show the same logical table through file, engine, index, and metadata views. |
| COBOL and fixed records | Course-history bridge | `COBOL` | `HIST-010` COBOL and Connected Computers | `runtime_defined`, `case_registered` | Connect exported `STUDENTS` data to fixed-record COBOL exercises. |
| ERP and industrial data | Database systems bridge | `ERP`, `SQL`, barcode/auto-id case material | `HIST-070`, `HIST-080` | `case_registered`, `needs_source_review` | Keep historical claims review-gated; later attach runtime simulations. |
| Help and self-documentation | `EDUCATIONAL_USE`, `TESTING` | `HELP`, `DOTHELP`, `CMDHELP`, `CMDHELPCHK`, `MAINT CONTRACTS` | `ENG-040`, `HIST-090` | `runtime_defined`, `runtime_lab_candidate` | Create the "comment to contract to HELP to proof" lab. |
| Testing and regression | `TESTING` | `CMDHELPCHK`, scripts, canaries, smoke tests | `ENG-010` through `ENG-050` | `runtime_defined`, `runtime_lab_candidate` | Teach testing as evidence, not just pass/fail. |
| Extension and student commands | EDREF extension idea, Teaching Point Ledger | `STUDENT HELLO`, `STUDENT ECHO`, `fn_student_text_autoreg` | Teaching point TP-20260528-003 | `curriculum_seed`, `runtime_defined_review` | Convert into a student extension lab after contract shape review. |
| Algorithms laboratory | `INDEX`, `ORDER`, `TESTING` | `IDX`, `SIX`, `SNX`, sort/index helpers | Teaching point TP-20260528-002 and TP-20260528-004 | `curriculum_seed` | Define timed sort/index labs without changing core index guarantees. |

## Initial Lab Paths

### Path 1: Database Literacy Starter

Goal: teach records, fields, tables, order, search, and output.

Evidence path:

```text
EDREF INTRO/MODEL
-> USE STUDENTS
-> FIELDS / STRUCT
-> LIST
-> SET INDEX / SET ORDER
-> SEEK or SCAN
-> CASE SHOW ENG-010 or ENG-020
```

Promotion gate:

```text
student_ready only after runtime transcript and HELP/CMDHELP readback are attached.
```

### Path 2: Self-Documenting Systems

Goal: teach that a working system can explain and check itself.

Evidence path:

```text
source comment
-> @dottalk.usage v1
-> comments SRC* evidence
-> CMDHELP BUILD artifacts
-> CMDHELP topic
-> CMDHELPCHK validation
-> LabTalk lesson
```

Promotion gate:

```text
Keep comments evidence, HELP build, validation, and router proof separate.
```

### Path 3: Historical Data Systems

Goal: teach database history through live or simulated labs.

Evidence path:

```text
HIST-000 Data Trail Overview
-> HIST-010 COBOL
-> HIST-020 JUMPS / 73C
-> HIST-030 CODASYL / ALCOA
-> HIST-040 xBase platform
-> HIST-070 ERP / SQL / Auto-ID
-> HIST-090 LabTalk and AI future
```

Promotion gate:

```text
Historical cases must separate personal source memory, reviewed source documents,
runtime simulation, and student-facing claims.
```

## Gaps

- `CIS101` is not yet a repo vocabulary term.
- `CS101` exists mostly as curriculum-source text, not as a runtime catalog.
- `EDREF` has strong concept coverage, but it is not yet cross-indexed to case IDs.
- Runtime education commands exist, but many need student-facing proof transcripts.
- Legacy curriculum material is valuable but intentionally quarantined until reviewed.
- The student curriculum packet is still a shell.

## Recommended Next Work

1. Add stable topic IDs to this map.
2. Generate a CSV version for tooling.
3. Add EDREF-to-case references where the runtime catalog can consume them.
4. Create three proof transcripts: starter database lab, self-documenting systems lab,
   and historical data systems lab.
5. Promote only proof-backed rows into the student manual.

## Working Definition

```text
LabTalk education is a campus map from foundational computing concepts to live
DotTalk++ evidence: concepts, commands, data, cases, contracts, help, validation,
and student labs.
```
