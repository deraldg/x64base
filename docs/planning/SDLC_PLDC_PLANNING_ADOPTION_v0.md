# SDLC / PLDC Planning Adoption v0

Status: maintained planning scaffold
Created: 2026-07-04
Scope: LabTalk Laboratory Campus, DotTalk++ SDLC, and future Planner/MS Project/OpenProject adoption

## Purpose

This document defines how the maintained SDLC and PLDC diagrams should later
become task plans, boards, schedules, and exportable planning artifacts.

The diagrams are source-controlled doctrine and planning maps. Planning software
will be a working surface over them, not the source of truth.

## Maintained Sources

| Area | Maintained source | Planning role |
|---|---|---|
| LabTalk SDLC | `D:/code/ccode/labtalk/LABTALK_SDLC_FRAMEWORK_v0.md` | Campus truth-state, labs, cases, datasets, portal, proof registry. |
| LabTalk diagrams | `D:/code/ccode/labtalk/diagrams/LABTALK_SDLC_DIAGRAMS_v0.md` | Visual board for real/dev/plugged/planned campus status. |
| DotTalk++ SDLC | `D:/code/ccode/docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md` | Runtime/system engineering lifecycle. |
| DotTalk++ diagrams | `D:/code/ccode/docs/maintenance/diagrams/DOTTALKPP_SDLC_DIAGRAMS_v0.md` | Visual board for runtime evidence, maintenance lanes, proof gates. |
| Website view | `D:/dev/x64base-IIS/content/docs/labtalk/sdlc.mdx` and `D:/dev/x64base-IIS/content/docs/dottalk/sdlc.mdx` | Public-facing summary, not authority. |

## Planning Levels

| Level | Example | Planning software mapping |
|---|---|---|
| Portfolio | x64base / DotTalk++ / LabTalk | Plan or roadmap. |
| Program | Laboratory Campus, DotTalk++ Runtime SDLC, Maintenance SDLC | Bucket, phase, or summary task. |
| Product/Lab | Database Literacy Starter, SelfDoc First Lab, Case Study Pack | Epic or summary task. |
| Work package | Add datasets registry, attach CMDHELP proof, build status report | Task. |
| Proof gate | Runtime transcript, CMDHELPCHK pass, case review closure | Milestone/checklist. |
| Publication gate | Website page, manual section, public diagram | Milestone/checklist. |

## Suggested Buckets

For Microsoft Planner:

```text
Intake
Design
Implementation
Proof
Review
Promotion
Maintenance
Publication
```

For Microsoft Project or OpenProject:

```text
1. LabTalk Campus SDLC
2. DotTalk++ Runtime SDLC
3. Maintenance SDLC
4. PLDC Product/Lab Packages
5. Publication and Website
```

## Required Task Fields

Any future exported task should preserve these fields:

```text
id
title
area
owning_lifecycle
truth_state
proof_state
risk_class
source_path
website_path
next_gate
owner
status
target_date
```

## Adoption Rule

Do not let a Planner bucket, Project task, or website page become the authority.

Authority order:

```text
source/runtime proof
-> SDLC charter/framework
-> maintained diagram/source document
-> planning software task
-> website/publication view
```

## First Import Candidates

| Task id | Title | Lifecycle | Bucket |
|---|---|---|---|
| PLAN-001 | Add LabTalk SDLC diagrams to maintained repo shelf | LabTalk SDLC | Promotion |
| PLAN-002 | Add DotTalk++ SDLC diagrams to maintenance diagram shelf | DotTalk++ SDLC | Promotion |
| PLAN-003 | Publish public SDLC summary pages to local x64base website | PLDC | Publication |
| PLAN-004 | Create case-study promotion matrix from `docs/cases/REGISTRY_CASES_v0.md` | LabTalk SDLC | Design |
| PLAN-005 | Create tools registry for portal/report/proof/publication tools | LabTalk SDLC | Design |
| PLAN-006 | Create DotTalk++ SDLC status report | DotTalk++ SDLC | Proof |
| PLAN-007 | Define release profiles: ENGINE, PROFESSIONAL, EDUCATIONAL, DEV_ONLY, MAINTENANCE | DotTalk++ SDLC | Design |
