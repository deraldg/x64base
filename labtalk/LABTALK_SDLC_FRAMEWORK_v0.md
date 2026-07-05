# LabTalk SDLC Framework v0

Status: draft operating framework
Created: 2026-07-04
Scope: Laboratory Campus delivery, proof, release, and truth-state governance

## Purpose

This framework defines how LabTalk Laboratory Campus work moves from idea to
student-ready material without overstating what exists.

LabTalk is not a single application. It is a campus layer over DotTalk++ runtime
evidence, source contracts, cases, datasets, labs, proof reports, and future UI
frontends. The SDLC therefore tracks both software delivery and educational
truth state.

The core rule is:

```text
Every student-facing claim must be real, development-only, plugged/stubbed, or
planned, and the label must point to evidence or a next gate.
```

## Truth-State Vocabulary

Use these labels in registries, reports, portal displays, lab docs, and release
notes.

| Label | Meaning | Allowed use |
|---|---|---|
| `real` | Working behavior exists in current repo/runtime/docs and has direct evidence. | May be used in demos and student material when proof is linked. |
| `dev` | Implementation exists but is not yet promoted for stable student use. | May be used by developers, instructors, or advanced labs with caveats. |
| `plugged_stubbed` | Entry point, registry row, command shell, UI hook, or placeholder exists, but behavior is partial, simulated, or delegated. | May be visible only with explicit stub wording and next gate. |
| `planned` | Design intent is documented, but no working entry point or proof exists yet. | May appear in roadmap and planning docs only. |
| `retired_or_superseded` | Prior artifact exists but is no longer the intended path. | Keep for historical trace, not for new labs. |

These labels complement the existing proof states in
`D:/code/ccode/labtalk/registries/proofs.yaml`.

## SDLC / PLDC Decision

LabTalk should use both SDLC and PLDC, but they should not mean the same thing.

Recommended split:

| Frame | Owns | Purpose |
|---|---|---|
| DotTalk++ SDLC | Runtime, source, build, commands, storage, indexing, HELP, metadata, tests, maintenance. | Keep the engine and professional runtime correct, buildable, testable, and safe. |
| LabTalk SDLC | Laboratory Campus docs, labs, cases, datasets, portal, proof registry, student-facing claims. | Keep the campus truthful, reviewable, and proof-backed. |
| PLDC | Products, labs, lessons, case-study packages, dashboards, public pages, class/workshop offerings. | Move a usable learning/product package from concept to delivery and support. |

Decision:

```text
DotTalk++ is large enough to deserve its own SDLC.
LabTalk uses its own campus SDLC.
PLDC sits above both as the product/lab delivery cycle.
```

PLDC should not replace SDLC. PLDC answers: "What package are we delivering,
to whom, and how will they use it?" SDLC answers: "What system behavior exists,
how is it controlled, and what proof keeps it trustworthy?"

## Lifecycle Stack

The Laboratory Campus is a stack of related but separate lifecycles.

| Layer | Lifecycle | Example output | Gate |
|---|---|---|---|
| Engine | x64base / storage SDLC | DBF/x64, indexes, memo, locks, row codecs. | Build, tests, runtime proof, data safety. |
| Runtime | DotTalk++ SDLC | Commands, shell, HELP, SQL, relations, scripts, MAINT. | Source review, command proof, HELP/CMDHELPCHK, smoke tests. |
| Maintenance | Maintenance SDLC | SelfDoc, contracts, manualgen, datadict, messaging, reports. | Report-only default, explicit mutation gate. |
| Campus | LabTalk SDLC | Labs, cases, datasets, proof registry, portal, diagrams. | Truth-state label, proof link, review state. |
| Product/lab | PLDC | Database Literacy Starter, SelfDoc First Lab, case-study modules, public pages. | Audience, package boundary, support/cleanup, release notes. |

Use the lowest applicable lifecycle as authority. For example, a LabTalk lesson
can present `SEEK`, but DotTalk++ SDLC owns whether `SEEK` actually behaves
correctly.

## Current Campus State

| Area | Current label | Evidence | Next gate |
|---|---|---|---|
| DotTalk++ runtime systems lab | `real` | `app.dottalkpp.runtime` in `registries/apps.yaml`; source under `D:/code/ccode/src`; runtime-evidenced command crosswalk in `labtalk/reports/selfdoc/x64base_engine_feature_crosswalk_v1.md`. | Keep command proofs current after runtime changes. |
| HELP / CMDHELP / CMDHELPCHK lab | `real` | `app.dottalkpp.help`; `proof.help.cmdhelp_source_exists`; `proof.lab.selfdoc.comments_to_contracts.first_run`; source under `src/cli/cmdhelp.cpp` and `src/cli/command_helpchk.cpp`. | Promote additional command families only after CMDHELPCHK or classified proof. |
| Self-documenting systems lab | `dev` | `lab.selfdoc.comments_to_contracts` is `first_runnable`; first proof is `validated`; crosswalk exists at `labtalk/reports/selfdoc/lab_selfdoc_first_crosswalk_v0.md`. | Review proof artifact and expand beyond CMDHELP/CMDHELPCHK. |
| Database literacy starter lab | `dev` | `lab.database_literacy.starter`; first run proof is `runtime_observed`; DTS script and lab doc exist. | Add table-backed STUDENTS/TEACHERS readback and HELP/CMDHELP proof. |
| Historical data systems trail | `plugged_stubbed` | `lab.history.data_systems_trail`; cases are registered; some historical cases are stubs or hidden until review. | Separate live runtime demos from simulated historical lessons and close source/fact/media review. |
| Case library | `dev` | `app.labtalk.case_library`; `LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md`; `LABTALK_CASE_REVIEW_V2.md`; runtime-loadable cases report green structure. | Complete review gates before publication or student-ready promotion. |
| Dataset library | `plugged_stubbed` | `app.labtalk.dataset_library` exists; registry points to expected data roots. | Add `datasets.yaml`, specimen checksums, and lab-safe fixture policy. |
| LabTalk portal | `dev` | `labtalk/portal/labtalk_portal.py`; `registries/portal.yaml`; `launch_portal.ps1`; first runtime captures in `labtalk/proofs/runs`. | Add case/dataset readback, command output capture, and proof dashboard view. |
| Proof dashboard | `planned` | Architecture defines the building; proof registry exists. | Generate first status report from registries and proof files. |
| Static campus HTML snapshot | `planned` | Listed as P2 portal future form. | Build from registries after P1 portal readback is stable. |
| DotTalk++ native `LABTALK` command | `planned` | Architecture says decide after registries stabilize. | Do not add until portal/registry model proves useful. |
| Jupyter / LMS delivery | `planned` | Architecture explicitly defers LMS; notebooks only where live exploration helps. | Revisit after campus data model is stable. |

## Laboratory Campus Asset Map

Lab Camp / Laboratory Campus should be treated as a campus of assets, not only
as a folder named `labtalk`.

| Asset family | Current roots | Truth-state owner | Notes |
|---|---|---|---|
| Campus doctrine | `labtalk/*.md` | LabTalk SDLC | Architecture, education map, portal concept, SDLC framework, developer profile. |
| Registries | `labtalk/registries` | LabTalk SDLC | Apps, labs, concepts, proofs, portal. Add datasets/cases/tools registries as needed. |
| Labs | `labtalk/labs` | LabTalk SDLC + PLDC | A lab is a deliverable package; it needs setup, run path, proof, review, cleanup. |
| Case studies | `docs/cases`, `labtalk/reports`, source DOCX evidence | LabTalk SDLC + case review | CASE_*.md files are runtime-readable derivatives, not source truth by themselves. |
| Proofs | `labtalk/proofs`, `docs/cases/runtime_proofs` | Proof lane | Proof must be reproducible or explicitly classified as historical/manual review. |
| Tools | `tools`, `labtalk/portal`, `scripts`, `src/maintenance` | Owning SDLC by behavior | Report-only tools stay lower risk; mutating tools require explicit gates. |
| Diagrams/media | `labtalk/diagrams`, `docs/media`, case media registries | PLDC + review | Useful for teaching, but diagrams do not replace source/runtime proof. |
| Public pages | website/content exports outside this repo | PLDC + publication review | Publication is downstream from proof and review, not a source of truth. |

## Case Study Lifecycle

Case studies need their own path inside the LabTalk SDLC because they mix
history, source memory, media, runtime proof, and student-facing explanation.

Case-study states:

| State | Meaning | Promotion gate |
|---|---|---|
| `source_memory` | Personal recollection or resume-derived context captured. | Mark as source memory; do not publish as verified history. |
| `source_document_seen` | Source file, transcript, deck, or external evidence identified. | Record path, owner, and review status. |
| `normalized_case_draft` | CASE_*.md derivative exists. | Loader/readback succeeds; source boundary is stated. |
| `runtime_readable` | DotTalk++ CASE loader can read it. | Runtime command proof or catalog readback exists. |
| `lab_candidate` | Case can support a lab. | Learning objective, dataset/tool path, and proof plan exist. |
| `reviewed_case` | Source/fact/media review is closed enough for controlled use. | Reviewer decision recorded. |
| `student_case` | Ready for learners. | Exercise, expected observations, risk notes, and proof links complete. |
| `publication_case` | Ready for website/manual/deck use. | Publication rights, source/fact/media review, and final copy review complete. |

Case-study rule:

```text
CASE_*.md may be runtime-readable before it is student-ready.
Runtime-readable is not the same as historically verified or publication-ready.
```

Initial case-study clusters:

| Cluster | Cases | Intended lab direction |
|---|---|---|
| Data trail overview | HIST-000, HIST-090 | Explain why LabTalk exists and how proof-backed learning works. |
| Army finance / JUMPS | HIST-020 | Payroll, records, batch systems, military finance, audit trails. |
| COBOL / connected computers | HIST-010 | Fixed records, batch processing, sequential files, early business systems. |
| CODASYL / Alcoa | HIST-030 | Network databases, payroll scheduling, industrial data pressure. |
| xBase / Earthkids / Paxon | HIST-040, HIST-050, HIST-060 | xBase apps, small-business systems, title/escrow conversion, DBF migration. |
| ERP / Hynix / SAP | HIST-070, HIST-080 | ERP, SQL, HR/Finance, process data, data migration and integration. |
| Engineering runtime cases | ENG-010 through ENG-050 | Indexing, seek/scan, buffering, metadata, file-to-engine separation. |

## Tool Lifecycle

Tools in the Laboratory Campus need explicit classification because some are
teaching aids, some are report generators, and some can mutate data or source.

| Tool class | Examples | Default state | Gate |
|---|---|---|---|
| Portal launcher | `labtalk/portal/labtalk_portal.py` | `dev` | May open docs and run approved scripts; missing paths must report clearly. |
| Report scanner | `tools/contracts/contract_scan.py`, metacollect reports | `real` or `dev` by proof | Read-only by default; output must state authority limits. |
| Proof runner | DTS scripts, lab PowerShell wrappers | `dev` until transcript exists | Must capture command, path, return code, and output location. |
| Fixture mutator | write labs, import/export repair tools | `planned` or `dev` | Must use disposable fixtures and rollback notes. |
| Runtime command | DotTalk++ C++ command handlers | DotTalk++ SDLC | Owned by DotTalk++ SDLC, not LabTalk docs. |
| GUI/workbench | Tkinter, wxWidgets, TUI, browser views | PLDC + owning SDLC | Must declare whether it is preview, dev, or maintained. |
| Publication generator | manualgen, static campus HTML | PLDC + maintenance SDLC | Publication does not replace source/runtime authority. |

Tool record fields to add when a tools registry is created:

```yaml
id:
name:
class:
path:
owning_lifecycle: dottalkpp_sdlc | labtalk_sdlc | maintenance_sdlc | pldc
truth_state:
risk_class:
inputs:
outputs:
mutation_policy:
proof:
next_gate:
```

## SDLC Lanes

### 1. Intake Lane

Captures new ideas, AI suggestions, historical notes, source observations, and
teaching requests without promoting them.

Inputs:

- AI Friendly intake items.
- Source comments and contracts.
- MDO/manualgen packets.
- Lab ideas from instructors or developers.
- Case source material and media notes.

Required fields:

```text
id
title
requested_by_or_source
campus_area
truth_state
evidence_links
next_gate
owner_or_reviewer
```

Exit gate:

```text
The item has a stable ID, a campus lane, and a truth-state label.
```

### 2. Design Lane

Turns accepted intake into bounded campus work.

Required artifacts:

- Registry row or planned registry row.
- Boundary statement.
- Runtime/source/doc surfaces affected.
- Proof plan.
- Student-facing risk classification.

Exit gate:

```text
The work can say what it will touch, what it will not touch, and how proof will
be captured.
```

### 3. Implementation Lane

Builds the smallest useful slice.

Allowed first forms:

- Markdown lab or architecture doc.
- YAML registry entry.
- Python report or portal action.
- DotTalk++ DTS script.
- C++ runtime hook only when registry/portal/report approach is insufficient.

Exit gate:

```text
The work runs or renders locally, or is explicitly marked plugged/stubbed with a
visible missing-behavior note.
```

### 4. Proof Lane

Attaches evidence before promotion.

Acceptable proof types:

- Runtime transcript.
- DTS command run capture.
- HELP/CMDHELP readback.
- CMDHELPCHK or validator output.
- Source-defined contract scan.
- Case registry load/readback.
- File checksum or fixture manifest.
- Manual review packet.

Exit gate:

```text
The proof is stored under a stable path, referenced from a registry or report,
and classified with a proof state.
```

### 5. Review Lane

Separates engineering correctness from student readiness.

Review checks:

- Runtime behavior matches the doc.
- Historical claims are sourced or clearly marked as interpretation.
- Simulated material is labeled as simulated.
- Case/media/dataset references resolve.
- Commands are safe for the intended audience.
- Mutation, filesystem, external process, and network risks are disclosed.

Exit gate:

```text
Reviewer can approve promotion, keep as dev, keep as plugged/stubbed, or return
to design with a concrete blocker.
```

### 6. Promotion Lane

Moves reviewed work to a stronger audience level.

Promotion levels:

| Level | Audience | Requirement |
|---|---|---|
| `developer_visible` | Maintainers and implementers. | Stable ID and design boundary. |
| `instructor_preview` | Instructors and advanced students. | Runnable or reviewable proof attached. |
| `student_ready` | General learner use. | Proof, review, safe setup, expected observations, and rollback/cleanup notes. |
| `publication_ready` | Website/manual/deck export. | Student-ready plus source/factual/media review where applicable. |

### 7. Maintenance Lane

Keeps LabTalk truthful as DotTalk++ and docs change.

Triggers:

- Runtime command behavior changes.
- HELP/CMDHELP/CMDHELPCHK changes.
- Case registry changes.
- Dataset fixture changes.
- Portal behavior changes.
- Manualgen or website publication changes.
- Any generated report changes status language.

Required maintenance action:

```text
Refresh affected proofs or demote the item from real/student-ready to dev or
plugged_stubbed.
```

## Promotion Matrix

| From | To | Required gate |
|---|---|---|
| `planned` | `plugged_stubbed` | Entry point or registry row exists, with missing behavior clearly stated. |
| `planned` | `dev` | Runnable implementation exists but proof/review is incomplete. |
| `plugged_stubbed` | `dev` | Stub path now performs useful behavior and has local run evidence. |
| `dev` | `real` | Runtime/source/doc evidence exists and is linked. |
| `real` | `student_ready` | Review confirms setup, safety, expected results, and proof are suitable for learners. |
| `student_ready` | `publication_ready` | Publication contract, factual review, and media/source rights checks are closed. |
| Any | Lower state | Evidence becomes stale, command behavior changes, proof breaks, or review finds drift. |

## Required Registry Additions

Existing registries already carry `status`, `proof_state`, `proof`, and
`next_gate`. Add these fields as files are next touched:

```yaml
truth_state: real | dev | plugged_stubbed | planned | retired_or_superseded
sdlc_lane: intake | design | implementation | proof | review | promotion | maintenance
audience_level: developer_visible | instructor_preview | student_ready | publication_ready
risk_class: read_only | writes_fixture | mutates_repo | launches_external | networked | historical_claim
review_gate: open | blocked | passed | waived_with_reason
last_verified: YYYY-MM-DD
```

Do not bulk-edit every registry only to add fields. Add them when a lane is
being actively worked or when a report generator can update them safely.

## Release Checklist

Use this checklist before calling any LabTalk item `student_ready` or
`publication_ready`.

```text
[ ] Stable ID exists.
[ ] Truth state is not planned or plugged_stubbed.
[ ] Lab/doc says what is real, dev-only, simulated, or historical.
[ ] Runtime or source proof is linked.
[ ] Setup instructions are local and repeatable.
[ ] Expected observations are stated.
[ ] Failure modes are classified.
[ ] Mutating commands use fixtures or explicit safeguards.
[ ] Historical claims have source/fact review or are labeled review-needed.
[ ] Portal/registry display agrees with the lab document.
[ ] Review decision is recorded.
```

## First 30-Day SDLC Backlog

1. Add `truth_state` to the active lab registry rows when those rows are next
   edited.
2. Create `datasets.yaml` for STUDENTS and TEACHERS with fixture path,
   mutability policy, and checksum/status placeholders.
3. Generate a LabTalk status report from `apps.yaml`, `labs.yaml`, and
   `proofs.yaml`.
4. Add portal display of `truth_state`, `proof_state`, and `next_gate`.
5. Attach HELP/CMDHELP readback to the Database Literacy Starter.
6. Close the first SelfDoc lab review and decide whether it becomes
   `instructor_preview`.
7. Keep Historical Data Systems Trail explicitly `plugged_stubbed` until live
   demos and simulated lessons are separated.
8. Create a case-study promotion matrix from `docs/cases/REGISTRY_CASES_v0.md`
   using the case lifecycle above.
9. Create a tools registry for portal, proof runners, report scanners,
   fixture-mutating tools, and publication generators.
10. Keep DotTalk++ SDLC in `docs/maintenance` and link LabTalk records to it
    instead of moving runtime governance into the campus docs.

## Non-Negotiables

- Do not market planned work as real.
- Do not treat a registry row as proof.
- Do not treat a successful command listing as behavioral proof unless the
  behavior itself is exercised.
- Do not let historical case prose become student-ready without review.
- Do not mutate DotTalk++ runtime behavior from LabTalk docs or portal actions
  unless the change has its own implementation and proof lane.
- Prefer demotion over ambiguity when evidence is stale.
- Do not use PLDC to bypass SDLC gates.
- Do not let LabTalk claim ownership over runtime behavior that belongs to
  DotTalk++ SDLC.
