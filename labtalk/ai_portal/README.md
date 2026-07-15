# AI Portal Hardening Lane

Status: **Alpha/Experimental — active lane**
Started: 2026-07-12
Owner: Laboratory Campus / AI Friendly / DotTalk++ integration

## Purpose

The AI Portal is a machine-facing orientation and context system for AI
development partners. It prepares a new or resumed AI for a specific project
task using explicit authority, contracts, runtime evidence, proof states, safety
gates, and task recipes.

It is not:

- a student portal for consuming an AI service;
- an autonomous source of project truth;
- standing permission to mutate, build, stage, commit, push, or publish;
- a replacement for DotTalk++ SDLC, LabTalk SDLC, contracts, HELP, SelfDoc, MDO,
  manualgen, or publication review.

## Canonical Startup

Do not use the reference shelf below as a competing first-read queue.

Start at repository-root `AI_README.md`, which defines the one canonical order:
newest closeout, current target, authority seeds, local-access checklist where
applicable, SDLC entry, contract preflight, and DotScript readiness.

## Reference Shelf — Depth on Demand

Read only the items required by the assigned task:

| Area | Reference |
| --- | --- |
| Authority and publication chain | `DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` |
| Acting-agent failure modes | `LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` |
| Owning lifecycle and task state | `SDLC_FAST_START_SEED_V1.md` |
| Source mutation preflight | `SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md` |
| DotScript readiness | `DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md` |
| Hosted/outside AI handoff | `EXTERNAL_AI_CHANGE_PACKAGE_V1.md` |
| Promotion mechanics | `PROMOTION_MODEL_SEED_V1.md` |
| Seed connection prototype | `SEED_CONNECTION_PROTOTYPE_NOTE_V1.md` |
| Shell/loop architecture | `../diagrams/DOTTALKPP_SHELL_DISPATCH_AND_LOOP_CAPTURE_V1.md` |
| Portal implementation | `../portal/README.md` |
| LabTalk lifecycle | `../LABTALK_SDLC_FRAMEWORK_v0.md` |
| Recursive co-development doctrine | `../docs/co-development/recursive_coproject_model_v1.md` |
| Typed registry and gate status | `../registries/ai_portal.yaml` |
| Older assimilation context | `../../docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md`, `AI_ASSIMILATION_BOOK_V1.md` |

## Working Model

```text
task request
-> classify project, lifecycle, lane, truth, proof, and risk
-> follow explicit task-to-seed requirements
-> verify authority and public baseline
-> select the smallest sufficient evidence set
-> explain every selected connection
-> expose missing or contradictory context
-> produce a bounded inspectable task packet
-> require explicit permission before guarded action
-> capture proof and readback
-> route durable results to contracts, SelfDoc, MDO, LabTalk, or publication
```

The portal organizes and packages truth; it does not manufacture it.

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
SelfDoc preserves provenance.
MDO/manualgen assembles reviewed documentation.
The AI Portal selects and explains task-relevant context.
```

## Authority Boundary

```text
D:\code\ccode -> C:\x64base -> github.com/deraldg/x64base
development      disposable    public snapshot
authority        staging
```

Original implementation belongs in authoritative development. Public `main` is
the baseline available to outside AI, not authority over unpublished development.
A new chat is not permission to create, switch, rename, or reset a branch.

## Delivery Posture

The lane is delivered as bounded, reviewable increments:

- **First useful surface:** authority seeds, task recipes, readiness probes, and
  explicit proof states.
- **Near-term prototype:** deterministic selection of the smallest required seed
  set, with reasons, conflicts, omissions, and readiness shown.
- **Hardened target:** guarded execution through reviewed, risk-classified
  adapters and explicit approval gates.
- **Full intent:** x64base-backed curation, portable recovery, and a teaching and
  evaluation loop.

## Current Gates

| Gate | State | Objective |
| --- | --- | --- |
| APH-0 Preserve and Stabilize | in progress | reproducible startup, zero unexplained missing paths, registry/audit baseline |
| APH-1 Typed Registry Graph | pending | typed nodes/edges, referential integrity, broken-fixture diagnostics |
| APH-2 Task Context Compiler | pending | deterministic bounded context packets with visible selection reasons |
| APH-3 Guarded Execution | pending | read-only default, capability/path controls, timeout, cancellation, redaction, transcripts |
| APH-4 Task-Centered Experience | pending | task-first GUI/CLI packet preparation and readiness views |
| APH-5 x64base Self-Hosting | pending | deterministic import/export, recovery proof, degraded read-only startup |
| APH-6 Teaching and Evaluation | pending | portal lessons and reproducible cold-start evaluation |

The typed registry is `labtalk/registries/ai_portal.yaml`. Registry rows and
probes do not by themselves prove runtime behavior.

## Mandatory Public Status

All portal, manual, website, and generated-summary references must retain the
**Alpha/Experimental** label until graph validation, context sufficiency, guarded
execution, recovery, and evaluation gates are complete.

The portal must not be presented as autonomous memory, independent authority, or
a production AI runtime.

## Closeout

A state-changing portal task must:

- report development, staging, proof, commit, push, and website states separately;
- update `CURRENT_TARGET`, `AI_README`, dashboard, or intake queue when their
  described state changes;
- leave a dated closeout under `docs/maintenance/`;
- add that closeout to the dashboard Session Log;
- state the next gate and residual risk.
