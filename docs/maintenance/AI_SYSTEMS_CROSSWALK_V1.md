# AI Systems Cross-Walk v1

Status: **M0 maintained analysis; not a runtime registry**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycles: **DotTalk++ SDLC**, **LabTalk SDLC**, **maintenance SDLC**, and **PLDC**
Incorporated lanes: cataloged by the charter
SDLC lane: `design` (M0 analyze)
Owner: `member.derald`
Initial steward: `member.ai.codex.local`

## Purpose

Name the AI-related systems, records, transports, projections, and educational
consumers without turning convenience surfaces into authority. This document is
the reviewed M0 cross-walk. M2 will decide the canonical machine-readable graph
and generator; this file does not pre-empt that architecture decision.

## Component cross-walk

| Stable ID | Component | Responsibility | Canonical record or implementation | Owning lifecycle | Incorporating lifecycle | Current state | Authority class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ai.curation.friendly` | AI Friendly | capture, classify, distill, anchor, route, promote | `docs/ai-friendly/AI_FRIENDLY_WORKFLOW_V1.md` | maintenance SDLC | AI Systems Integration SDLC | seed | routing doctrine |
| `ai.portal.core` | AI Portal | proof-aware task context and guarded action architecture | `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md` | LabTalk SDLC | AI Systems Integration SDLC | alpha plan with implemented foundations | architecture and policy |
| `ai.state.tier0` | Tier 0 | generated current and perishable state | `labtalk/ai_portal/TIER0_STATE.md` | LabTalk SDLC | AI Systems Integration SDLC | generated | derived working state |
| `ai.seed.tier1` | Tier 1 | mandatory cold-start invariants and stopping test | `labtalk/ai_portal/AI_TIER1_SEED_V1.md` | LabTalk SDLC | AI Systems Integration SDLC | active | onboarding doctrine |
| `ai.graph.recall` | Portal recall graph | trigger-based retrieval of doctrine | `labtalk/registries/portal_recall_graph.yaml` | LabTalk SDLC | AI Systems Integration SDLC | implemented seed | retrieval index |
| `ai.work.aif_queue` | AIF intake queue | distilled candidates and lane status | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | maintenance SDLC | AI Systems Integration SDLC | active, drift-prone | prospective record |
| `ai.work.aif_claims` | AIF claim ledger | unique atomic AIF allocation | `coordination/aif/AIF-*.claim` | maintenance SDLC | AI Systems Integration SDLC | active | allocation record |
| `ai.coordination.sessions` | Session coordinator | live presence, contested-file locks, and AIF claims | `tools/coordination/session_coordinator.py` | maintenance SDLC | AI Systems Integration SDLC | active local tool | coordination, not authorization |
| `ai.coordination.worktrees` | Worktree lane isolation | physically isolate concurrent lane changes | `docs/maintenance/AI_WORKTREE_LANE_ISOLATION_LANE_V1.md` | DotTalk++ SDLC | AI Systems Integration SDLC | design-intended | coordination design |
| `ai.provenance.runs` | AI run registry | actor, project, lane, continuation, and closeout pointers | `labtalk/registries/ai_runs.yaml` | maintenance SDLC | AI Systems Integration SDLC | active candidate | durable run provenance |
| `ai.provenance.closeouts` | Session closeouts | what happened, evidence, remaining work, and authorization | `docs/maintenance/SESSION_CLOSEOUT_*.md` | declared per closeout | AI Systems Integration SDLC | active | episodic record |
| `ai.evidence.proofs` | Proof registry and transcripts | what was actually observed or verified | `labtalk/registries/proofs.yaml`, `labtalk/proofs/runs/` | declared per proof | AI Systems Integration SDLC | active | evidence |
| `ai.intake.external` | External AI intake | preserve and assess outside proposals | `docs/maintenance/external_ai_intake/` | maintenance SDLC | AI Systems Integration SDLC | active landing zone | source material, not authority |
| `ai.audit.reports` | AI report audit | actor/task/project/scope/Git provenance and validation | `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md` | maintenance SDLC | AI Systems Integration SDLC | mandatory | compliance record |
| `ai.memory.external` | External agent memory | memory classes, event lifecycle, and durable continuity model | `docs/maintenance/EXTERNAL_AGENT_MEMORY_LANE_V1.md` | maintenance SDLC | AI Systems Integration SDLC | design-intended | architecture proposal |
| `ai.transport.bbs` | AI-BBS | authenticated local boards and request/response transport | `src/bbs/`, `src/cli/cmd_bbs.cpp` | DotTalk++ SDLC | AI Systems Integration SDLC | runtime-observed, hardening open | transport, not authority |
| `ai.handoff.worklog` | BBS worklog | asynchronous pickup and drop-off convention | `docs/ai-friendly/AI_BBS_WORKLOG_HANDOFF_LANE_V1.md` | DotTalk++ SDLC | AI Systems Integration SDLC | source-defined small end | convenience handoff |
| `ai.pattern.pseudo_chat` | Pseudo-Chat | umbrella interaction pattern spanning several components | this cross-walk plus component records below | AI Systems Integration SDLC | AI Systems Integration SDLC | ambiguous legacy term | pattern, never system of record |
| `ai.projection.operations` | Internal AI operational views | human-readable generated status, rulings, boards, and access views | `docs/reports/`, report generators | maintenance SDLC | AI Systems Integration SDLC | local/internal; freshness varies | derived projection |
| `ai.public.reports` | Public Reports collection | reviewed public-interest reports, whitepapers, and research | future explicit publication manifest | source-owning SDLC per artifact | AI Systems Integration SDLC and PLDC | not yet separated | reviewed publication |
| `ai.public.website` | Public website AI area | reviewed public explanation and educational projection | website source and publication contract | PLDC | AI Systems Integration SDLC | alpha publication surface | publication, not development authority |
| `ai.education.labtalk` | LabTalk education | labs, lessons, cases, and worked SDLC examples | LabTalk registries and curriculum artifacts | LabTalk SDLC | AI Systems Integration SDLC | active campus | reviewed educational consumer |

## Pseudo-Chat decomposition

Pseudo-Chat remains an umbrella phrase. Records and interfaces use the specific
component name:

| Component | Meaning | System of record? |
| --- | --- | --- |
| External intake packet | durable addressed request or returned change package | Source material only; accepted state lives elsewhere. |
| Session coordination | presence, lane claim, file lock, worktree | No; coordinates actors. |
| BBS transport | authenticated socket request/response | No; transports messages. |
| Worklog handoff | asynchronous lane pickup/drop-off post | No; closeout and registries remain authoritative. |
| Guest message | narrowly scoped unaffiliated input | No; intake requiring review. |
| Duplex chat | future concurrent interactive exchange | Not implemented and not authoritative. |

## Document and report classes

| Class | Examples | Publication posture |
| --- | --- | --- |
| `operational_projection` | AI Portal status, AIF open rulings, BBS boards, access map | internal/local by default; generated and freshness-labeled |
| `audit_record` | AI-authored closeout, assessment, external intake manifest | sensitivity reviewed; not public by default |
| `public_report` | reviewed public-interest technical report or research result | explicit allow-list and source review |
| `whitepaper` | stable argument or architecture paper for an academic audience | editorial, evidence, sensitivity, and publication review |
| `educational_case` | worked lifecycle case derived from actual project evidence | LabTalk review and proof links required |

The public navigation label **Reports** is reserved for `public_report`,
`whitepaper`, and reviewed `educational_case` material. Internal generated pages
belong under **AI Operations** or another explicitly operational label.

## Canonical transition path

```text
interaction or observation
-> candidate intake
-> classified project/lane work
-> authorized run
-> source or documentation change
-> proof
-> audited closeout and canonical status transition
-> generated operational projection
-> separately reviewed educational/public publication
```

Skipping a transition does not grant the state that would have been established
there. A BBS post cannot promote a lane. A generated report cannot prove runtime
behavior. A public page cannot change development authority.

## Known reconciliation obligations

1. AIF-082's intake row predates later delivered Tier 0, Tier 1, and recall work.
2. `ai_report_index.yaml` indexes only part of the discoverable report corpus.
3. `AIF_RULINGS_REPORT.html` derives from a ruling sheet, not all AIF records.
4. Older raw-report publication guidance conflicts with the current local-only
   posture.
5. Report names containing `latest` need generation time, source identity, and
   a staleness rule.
6. Pseudo-Chat records must identify which decomposed component actually carried
   the interaction.
7. AIF-064 is assigned to the Retro VM/emulator lane in the intake queue but to
   registry-fragment tooling in the tool and AIF-084 charter. The owner must
   reconcile that identity before either meaning is incorporated here.
8. The AIF-082 fast-start seed declares 20 mandatory task fields but enumerates
   19. AIF-086 preserves the 19 named fields and leaves the count/schema ruling
   with AIF-082.

## M2 machine-graph requirements

The later canonical graph must represent:

- stable component ID and label;
- owning and incorporating lifecycles;
- project and incorporated lane identities;
- authority class and system-of-record pointer;
- sensitivity and publication posture;
- freshness owner and regeneration trigger;
- typed directional edges;
- proof and acceptance requirements;
- supersession without deletion of historical evidence.

No new registry is declared canonical until that schema and migration are
reviewed.
