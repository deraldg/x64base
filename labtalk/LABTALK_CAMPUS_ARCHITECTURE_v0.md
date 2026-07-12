# LabTalk Campus Architecture v0

Status: draft architecture
Scope: LabTalk campus design, app collection model, registries, and implementation path
Created: 2026-07-02

## Working Definition

LabTalk is a living laboratory campus for computing education. It is a collection
of interoperating apps, cases, datasets, runtimes, GUIs, help systems, historical
simulations, contracts, and proof tools.

DotTalk++ is one major campus building: the runtime systems lab. LabTalk is the
campus that organizes many buildings, not a single C++ application.

Canonical Mission and Vision framing is maintained in:

```text
dottalkpp/docs/architecture/X64BASE_LABORATORY_CAMPUS_MISSION_VISION_V1.md
```

The AI Portal described by that document and tracked under
`labtalk/ai_portal` is **Alpha/Experimental**. It is a proof-aware context and
teaching lane, not production autonomous memory or a replacement authority for
source, runtime, HELP, metadata, contracts, or human approval.

## Design Goal

LabTalk should let a learner or developer move through this chain:

```text
concept -> app -> dataset -> command -> proof -> case -> lesson
```

This is the central campus pattern. A lesson should not be disconnected prose.
It should be backed by live or reviewed evidence.

## Influences

LabTalk should borrow selectively from several proven education models:

- Nand2Tetris: build and understand a system layer by layer.
- Jupyter/Data 8: mix explanation, live computation, datasets, and reproducible
  artifacts.
- Software Carpentry: use clear lesson structure, setup notes, exercises, and
  instructor-facing guidance.
- Moodle/Open edX: keep open-source LMS delivery in mind, but do not start with
  a full LMS dependency.

The first implementation should be lighter than an LMS and more structured than
a folder of notes.

## Campus Buildings

| Building | Purpose | Likely implementation |
|---|---|---|
| Campus Map | Entry point and navigation across apps/labs/cases. | Markdown/YAML first, later web UI. |
| Runtime Systems Lab | Teach live DotTalk++ state, commands, data, indexes, relations, and scripts. | C++ DotTalk++ runtime plus scripts/transcripts. |
| Historical Data Systems Lab | Teach database history from punch cards/COBOL/CODASYL/xBase/SQL/ERP/AI. | Case registry, simulated datasets, optional notebooks. |
| Self-Documenting Systems Lab | Teach comments, contracts, HELP, CMDHELP, CMDHELPCHK, SelfDoc, metadata. | DotTalk++ commands plus Python reports. |
| Dataset Library | Store and describe sample DBFs, fixed records, CSVs, SQL files, artifacts. | YAML registry plus filesystem assets. |
| Case Library | Normalize historical and engineering cases. | Existing `docs/cases` registry plus LabTalk index. |
| GUI Design Lab | Demonstrate GUI PLDC and multiple UI approaches over the same engine. | Web, Python/Tk, wxWidgets, or other GUI prototypes. |
| AI-Assisted Development Lab | Study coding contracts, AI branch flow, review, and proof. | Markdown contracts, source scans, transcript/proof reports. |
| Proof Dashboard | Show what is source-defined, runtime-proven, HELP-documented, reviewed. | Static report first, later local web dashboard. |

## Registry-First Model

The campus should be driven by small registries. These can start as Markdown and
YAML, then become DBF/SQLite/JSON exports if needed.

Recommended registries:

```text
apps.yaml
labs.yaml
cases.yaml
datasets.yaml
lessons.yaml
concepts.yaml
proofs.yaml
commands.yaml
artifacts.yaml
```

The registries should reference existing DotTalk++ sources rather than copy them.

## Canonical IDs

IDs should be stable, lowercase, and campus-scoped.

Examples:

```text
app.dottalkpp.runtime
app.dottalkpp.help
app.labtalk.campus_map
lab.database_literacy.starter
lab.selfdoc.comments_to_contracts
lab.history.cobol_to_xbase
case.eng_040.metadata_data_dictionary
dataset.students
proof.cmdhelp.help_topic
lesson.cs101.records_fields_tables
concept.database.index
```

Use stable IDs even while names change. Names are display text; IDs are contract.

## App Manifest Shape

Each app should eventually have a manifest:

```yaml
id: app.dottalkpp.runtime
name: DotTalk++ Runtime Systems Lab
kind: runtime_lab
status: active
languages:
  - c++
  - dotscript
entrypoints:
  - command: dottalkpp
  - source: D:/code/ccode/src
concepts:
  - concept.database.table
  - concept.database.index
  - concept.runtime.state
cases:
  - case.eng_010.index_navigation
  - case.eng_020.seek_vs_scan
proofs:
  - proof.runtime.command_smoke
  - proof.help.cmdhelp
```

## Lab Manifest Shape

Each lab should say what it teaches, what it runs, and what proof is required.

```yaml
id: lab.selfdoc.comments_to_contracts
title: Comments to Contracts to HELP
status: draft
audience:
  - student
  - developer
concepts:
  - concept.source.comments
  - concept.contract.usage
  - concept.help.runtime
apps:
  - app.dottalkpp.help
  - app.dottalkpp.selfdoc
commands:
  - HELP
  - CMDHELP
  - CMDHELPCHK
  - MAINT CONTRACTS
evidence:
  - include/edref.hpp
  - docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md
promotion_gates:
  - source_contract_exists
  - comments_evidence_readback
  - cmdhelp_artifact_exists
  - cmdhelpchk_pass_or_classified
  - student_transcript_attached
```

## Lesson Shape

Borrow the discipline from Software Carpentry, but keep LabTalk's proof model.

```text
Title
Audience
Prerequisites
Learning objectives
Concepts
Apps used
Dataset used
Commands used
Steps
Expected observations
Questions
Proof/evidence links
Instructor notes
Review status
```

Lesson pages should clearly separate:

- what the student does
- what the system proves
- what is simulated
- what is historical interpretation
- what is still under review

## Proof States

LabTalk needs explicit proof vocabulary so student-facing material does not drift
ahead of runtime reality.

| State | Meaning |
|---|---|
| `idea` | Concept captured, not reviewed. |
| `source_defined` | Current source declares behavior or contract. |
| `runtime_observed` | A transcript or smoke output exists. |
| `help_documented` | HELP/CMDHELP exposes it. |
| `validated` | CMDHELPCHK, SelfDoc, or another validator checked it. |
| `case_registered` | Case registry knows the teaching context. |
| `student_ready` | Reviewed for student use. |
| `simulated` | Demonstration is intentionally simulated, not live runtime. |
| `historical_review_needed` | Historical claim needs source/fact review. |

## Technology Choices

Start with boring, durable tools:

- Markdown for campus docs and lessons.
- YAML for registries.
- Python for index generation, validation, and report building.
- DotTalk++ CLI and DTS scripts for runtime proof.
- C++ only where LabTalk needs runtime hooks or DotTalk++ integration.
- Static HTML or a lightweight local web app for navigation.
- Jupyter notebooks only where live exploration clearly helps.

Avoid a full LMS dependency at the beginning. The reserved provider-neutral LMS
communications lane may queue local integration intent while the campus data
model stabilizes. Moodle is the first provider candidate; endpoints,
credentials, and live delivery remain future, separately approved work.

## First Implementation Slice

Milestone 1 should create the campus skeleton without touching DotTalk++ runtime
behavior.

Files:

```text
D:/code/ccode/labtalk/README.md
D:/code/ccode/labtalk/LABTALK_CAMPUS_ARCHITECTURE_v0.md
D:/code/ccode/labtalk/LABTALK_EDUCATION_MAP_v0.md
D:/code/ccode/labtalk/registries/apps.yaml
D:/code/ccode/labtalk/registries/labs.yaml
D:/code/ccode/labtalk/registries/concepts.yaml
D:/code/ccode/labtalk/registries/proofs.yaml
```

First app records:

```text
app.dottalkpp.runtime
app.dottalkpp.help
app.dottalkpp.selfdoc
app.labtalk.case_library
app.labtalk.dataset_library
```

First labs:

```text
lab.database_literacy.starter
lab.selfdoc.comments_to_contracts
lab.history.data_systems_trail
```

## First Three Labs

### 1. Database Literacy Starter

Purpose:

```text
Teach tables, records, fields, order, search, scan, and output.
```

Uses:

```text
EDREF INTRO/MODEL/TABLE_RECORD_FIELD/INDEX/SCAN
DotTalk++ USE/FIELDS/STRUCT/LIST/SET ORDER/SEEK/SCAN
STUDENTS and TEACHERS datasets
ENG-010 and ENG-020 cases
```

### 2. Comments to Contracts to HELP

Purpose:

```text
Teach how source comments become structured contracts and help/proof artifacts.
```

Uses:

```text
@dottalk.usage v1
comments SRC* tables
CMDHELP
CMDHELPCHK
MAINT CONTRACTS
ENG-040 case
```

### 3. Historical Data Systems Trail

Purpose:

```text
Teach database evolution from COBOL/fixed records through CODASYL, xBase,
SQL/ERP, and AI-era explainability.
```

Uses:

```text
HIST-000 through HIST-090 cases
COBOL command
CODASYL/REL ENUM material
xBase platform case
LabTalk AI future case
```

## Boundary Rules

- LabTalk may reference DotTalk++ source, HELP, cases, datasets, and proof
  artifacts.
- LabTalk should not silently mutate DotTalk++ runtime behavior.
- LabTalk C++ integration belongs under `D:/code/ccode/src/labtalk`.
- LabTalk planning and registry files belong under `D:/code/ccode/labtalk`.
- Historical and curriculum material must be labeled by evidence class.
- Student-facing claims require proof or an explicit simulation label.

## Near-Term Decisions

1. Choose registry format: YAML only, or YAML plus generated CSV.
2. Choose first campus UI: static generated HTML, local web app, or CLI index.
3. Decide whether Jupyter notebooks are part of v0 or deferred.
4. Decide whether LabTalk should have its own command in DotTalk++ now or after
   registries stabilize.
5. Decide whether cases remain mirrored from `docs/cases` or get a LabTalk
   overlay registry.

## Recommended Next Step

Create the v0 registry files and keep them small. The first goal is not a large
app. The first goal is a campus map that can answer:

```text
What labs exist?
What app runs them?
What concepts do they teach?
What datasets do they use?
What proof exists?
What is safe for students now?
```
