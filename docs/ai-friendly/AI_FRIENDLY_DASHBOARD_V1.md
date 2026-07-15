# AI Friendly Dashboard v1

Status: active seed dashboard.
Updated: 2026-07-15.
Purpose: user-visible status surface for AI-assisted DotTalk++ / LabTalk work.

## Current Visibility Contract

The user should be able to see what AI is working on, what evidence it read,
what it touched, whether mutation occurred, where material was routed, and what
still requires review, proof, promotion, or publication.

## Current Lane State

| Area | Status | Anchor |
| --- | --- | --- |
| AI Friendly lane | seeded and active | `docs/ai-friendly/README.md` |
| AI Portal hardening | **Alpha/Experimental — active** | `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md` |
| Canonical AI front door | promoted | `AI_README.md` |
| Closeout-updates-startup gate (AIF-006) | source-defined; manual enforcement | `AI_PORTAL.md` -> "Closeout Updates Startup" |
| Local-access agent checklist (AIF-009) | promoted | `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` |
| MCC databuild foundation | runtime-proven and publicly certified | `docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md` |
| xbase/xindex proof matrix (AIF-014) | development-runtime-proven; mutation hardening and public edition publication remain | `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` |
| Engine/product edition separation (AIF-015) | implemented and proven in authoritative development; public source pending Path A | `docs/maintenance/EDITION_PUBLICATION_PLAN_A_V1.md` |
| Cold-clone journey (AIF-016) | **published and certified** | commits `46e02159`, `b9d48021` |
| DEV-02 manual drift (AIF-017) | review-needed | per-section manual source + manualgen |
| Generated report integration | not started | future report under `docs/ai-friendly/reports` |

Public-state rule: `BUILDING.md` describes only what a fresh clone of `main`
contains. Development-only proof must be labeled as development-only until the
coherent source changeset is published and cold-clone certified.

## Session Log

Newest first. Each row is a durable closeout; chat is not the record.

| Date | Session | Lane state changed | Closeout |
| --- | --- | --- | --- |
| 2026-07-15 | AI Portal consistency reconciliation | Corrected stale public-state pointers, unique intake IDs, published cold-clone status, and development-versus-public edition wording on review branch `ai-portal-consistency-20260715`. | this review branch / PR |
| 2026-07-15 | Cold-clone journey certification | Certified clone -> `pro-md` build -> runtime staging -> MCC databuild -> ordered query; follow-up fixed DotScript inline comment syntax. | `docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md` |
| 2026-07-14 | x64base engine/edition separation implementation | Proved LEAN/NONE and other development profiles; public publication remains Path A. | `docs/maintenance/SESSION_CLOSEOUT_X64BASE_ENGINE_EDITION_SEPARATION_IMPLEMENTATION_2026-07-14.md` |
| 2026-07-14 | x64base engine/edition separation research | Separated product edition from index capability and recorded publication plan. | `docs/maintenance/SESSION_CLOSEOUT_X64BASE_ENGINE_EDITION_SEPARATION_RESEARCH_2026-07-14.md` |
| 2026-07-14 | xbase build proof continuation | Added pydottalk tests and physical-order CRUD proof; native index mutation hardening remains. | `docs/maintenance/SESSION_CLOSEOUT_XBASE_PROOF_MATRIX_2026-07-14.md` |
| 2026-07-14 | AI Portal outcome digestion and build architecture review | Established current build boundaries and portal doctrine. | `docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_BUILD_ARCHITECTURE_2026-07-14.md` |
| 2026-07-14 | MCC databuild, hygiene, and portal corrections | Runtime-proven databuild lane and AIF-006/AIF-008/AIF-009/AIF-010 foundations. | `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` |

## Status Buckets

| Bucket | Current items |
| --- | --- |
| draft | AIF-004, AIF-005 |
| anchored / routed | AIF-001, AIF-002, AIF-003, AIF-006, AIF-012, AIF-013 |
| promoted | AIF-008, AIF-009, AIF-010, AIF-016 |
| review-needed | AIF-011, AIF-017; AIF-012 privacy/history review |
| development-proven, publication pending | AIF-014, AIF-015 |
| rejected | AIF-007 |
| superseded | none |

The canonical row definitions and full notes live in
`docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.

## Authority Levels

| Level | Meaning |
| --- | --- |
| chat-only | Conversation material only. |
| captured | Saved for possible review. |
| draft | Written but not reviewed or proven. |
| design-intended | Accepted direction, not runtime proof. |
| source-defined | Current source declares or implements it. |
| runtime-proven | Test, transcript, command, or readback proves it. |
| HELP-documented | HELP/CMDHELP exposes it. |
| CMDHELPCHK-validated | Validation checked the HELP/contract surface. |
| publication-ready | Reviewed evidence can be published. |
| student-ready | LabTalk can present it to learners. |
| rejected | Reviewed and excluded. |
| superseded | Replaced by stronger material. |

## Items Needing Review or Proof

| Item | Needed work | Route |
| --- | --- | --- |
| AI Portal APH-0 | reproducible startup, registry audit, zero unexplained missing paths | `labtalk/ai_portal` |
| Typed registry graph and context compiler | APH-1 and APH-2 validation and deterministic packet proof | `labtalk/registries/ai_portal.yaml` |
| xindex mutation hardening | attached-index replace/append/delete/recall/pack synchronization and stale/collation rejection | `XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` |
| Edition publication | coherent source/build changeset, cold-clone profile matrix, merge to `main` | `EDITION_PUBLICATION_PLAN_A_V1.md` |
| DEV-02 manual | update per-section source and regenerate after public state is settled | manualgen lane |
| Developer profile | maintainer privacy/history review | AIF-012 |

## Next Practical Step

For runtime work, enter through the current assignment and complete the source
mutation contract preflight. For publication work, keep authoritative development,
disposable staging, public `main`, and website state separate. Do not claim the
edition system is in the public clone until Path A is completed and `BUILDING.md`
is updated after cold-clone certification.
