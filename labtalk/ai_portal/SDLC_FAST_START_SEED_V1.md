# AI Portal SDLC Fast-Start Seed v1

Status: **Mandatory for every AI Portal task**
Authority: maintained DotTalk++ SDLC, LabTalk SDLC, maintenance SDLC, and PLDC doctrine

## Rule

The AI Portal enters the existing SDLC. It does not create a parallel AI
workflow.

Before planning or changing anything, read the maintained lifecycle sources
needed for the task:

1. `D:\code\ccode\docs\maintenance\DOTTALKPP_SDLC_CHARTER_v0.md`
2. `D:\code\ccode\labtalk\LABTALK_SDLC_FRAMEWORK_v0.md`
3. `D:\code\ccode\docs\planning\SDLC_PLDC_PLANNING_ADOPTION_v0.md`
4. `D:\code\ccode\labtalk\ai_portal\SCOPE_CALIBRATION_SEED_V1.md`
5. the owning maintenance, product, proof, or publication lane documents

## Select the Owning Lifecycle

| Work | Owning lifecycle |
| --- | --- |
| Engine, runtime, storage, command, DotScript behavior, HELP, build, test | DotTalk++ SDLC |
| Contracts, SelfDoc, MDO/manualgen, metadata, guarded tools | Owning maintenance SDLC plus DotTalk++ SDLC when runtime is affected |
| LabTalk portal, registries, labs, cases, campus truth | LabTalk SDLC |
| Product, lab, workshop, release package, or public page | PLDC plus the underlying owning SDLC |

PLDC cannot promote behavior beyond its SDLC evidence. Publication does not
turn design intent into runtime proof.

## Mandatory Task Fields

Every AI task packet, outside-AI request, change package, and closeout must
preserve:

```text
id:
title:
area:
owning_lifecycle:
sdlc_lane: intake | design | implementation | proof | review | promotion | maintenance | publication
operating_mode: laboratory | production | maintenance | incident
change_class: C0 | C1 | C2 | C3 | C4
build_target: xbase_engine | dottalkpp_runtime | binding | frontend | documentation_only
product_profile: LEAN | PROFESSIONAL | EDUCATIONAL | DEVELOPMENT | not_applicable
index_profile: NONE | LEGACY | LMDB | inherited | not_applicable
scope_reason:
truth_state:
proof_state:
risk_class:
source_path:
website_path:
next_gate:
owner:
status:
```

Unknown fields must be marked unknown, not guessed.

## Gate Rule

Before implementation, identify requirements, boundaries, mutation and
compatibility risk, expected behavior, HELP/metadata impact, and proof path.
Treat the compiled x64base engine, the DotTalk++ runtime, product composition,
and index profile as separate scope axes. Do not assume full DotTalk++ or the
`DEVELOPMENT` profile when the actual target is xbase-only or lean.

Before promotion, require the smallest behavioral proof appropriate to the
change: build, targeted test, DotScript transcript, command output, fixture
readback, HELP/CMDHELP, CMDHELPCHK, scan, or before/after diff.

When that proof requires a full or long-running build, follow the mandatory
operator handoff in `DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`: provide the exact
PowerShell command and expected evidence, then wait for the maintainer's result.
Do not launch or babysit the build without explicit current-task authorization.
An interrupted, timed-out, or partially observed build does not pass the gate.

Before publication, confirm that public text does not outrun source, runtime,
contracts, HELP, or current proof state.

## Closeout Rule

Report:

- owning lifecycle and SDLC lane entered;
- entry state and gate;
- implementation and proof performed;
- review result;
- promotion/publication state actually reached;
- next open gate and residual risk.

An AI package, portal button, registry row, command listing, website page, or
successful build alone is not behavioral proof.
