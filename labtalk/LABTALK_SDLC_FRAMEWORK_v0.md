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

## Non-Negotiables

- Do not market planned work as real.
- Do not treat a registry row as proof.
- Do not treat a successful command listing as behavioral proof unless the
  behavior itself is exercised.
- Do not let historical case prose become student-ready without review.
- Do not mutate DotTalk++ runtime behavior from LabTalk docs or portal actions
  unless the change has its own implementation and proof lane.
- Prefer demotion over ambiguity when evidence is stale.

