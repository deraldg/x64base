# AI Interaction Intake Queue v1

Status: seed queue.

## Purpose

Track AI-assisted material that may deserve promotion into existing DotTalk++ /
LabTalk lanes.

This is not a raw chat archive. It is a review queue for distilled candidates.

## Queue Columns

Use this shape for new rows:

| ID | Source | Classification | Candidate route | Evidence anchor | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |

## Seed Rows

| ID | Source | Classification | Candidate route | Evidence anchor | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AIF-001 | AI Baby Bootstrap Card | agent_instruction, workflow_pattern | `docs/agents` | `docs/agents/AI_BABY_BOOTSTRAP_CARD.md` | anchored | Already active first-read seed; do not duplicate. |
| AIF-002 | Contract lifecycle chat-to-contract rule | contract_candidate, workflow_pattern | `docs/contracts` | `docs/contracts/CONTRACT_LIFECYCLE_V1.md` | anchored | Reuse existing lifecycle instead of creating a new AI authority model. |
| AIF-003 | LabTalk SelfDoc first lab | selfdoc_candidate, labtalk_candidate, proof_candidate | LabTalk, SelfDoc, proofs | `D:/code/ccode/labtalk/labs/self_documenting_systems/LAB_SELFDOC_COMMENTS_TO_CONTRACTS_v0.md` | anchored | Good model for report-only curation from source comments/contracts to HELP validation. |
| AIF-004 | AI Friendly lane proposal | workflow_pattern | `docs/ai-friendly` | `docs/ai-friendly/AI_FRIENDLY_LANE_MANIFEST_V1.md` | draft | Seed lane defining capture, classify, distill, anchor, route, promote. |
| AIF-005 | New-AI assimilation portal/book | agent_instruction, workflow_pattern, continuity_plan | `docs/ai-friendly`, `MAINT AI` | `docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md` | draft | Durable onboarding path if prior AI chat history or provider-hosted content is unavailable. |
| AIF-006 | Claude session 2026-07-13 (hosted, no repo access); re-evaluated 2026-07-14 with repo access | workflow_pattern, agent_instruction, drift_or_risk | `AI_PORTAL.md`, `AI_README.md`, `AI_ASSIMILATION_BOOK_V1.md` | `docs/agents/CURRENT_TARGET.md` drift, verified 2026-07-14 | anchored | **Closeout-updates-startup gate. MERGED 2026-07-14** by maintainer decision. A session that changes lane state must also update the AI-facing doc describing that state, or explicitly decline with a reason. Anchored by a real drift instance: CURRENT_TARGET.md named a nonexistent dir and called `C:\x64base` a backup. **Placement corrected on merge:** the 2026-07-13 draft proposed a *new* gate in `AI_FRIENDLY_WORKFLOW_V1.md`; rejected, because five closeout shapes already existed and a sixth violates the Simplification Rule. Instead folded into the three AI-facing closeout shapes: `AI_PORTAL.md` ("Closeout Updates Startup"), `AI_README.md` ("Closeout Shape"), `AI_ASSIMILATION_BOOK_V1.md` §15. Evidence class: Design-intended -> Source-defined (gate text present in all three). Not yet Runtime-proven; no automated check enforces it. |
| AIF-007 | Same session; withdrawn proposal | agent_instruction | — | `AI_PORTAL.md:69` Outside-AI Delivery Rule | rejected | Proposed a hosted-vs-local-access AI distinction. **Redundant** — the hosted case is already covered by the Outside-AI Delivery Rule and `EXTERNAL_AI_CHANGE_PACKAGE_V1.md`. The real gap was the inverse: no defined lane for an AI *with* local write access. Addressed 2026-07-14 by the "Local-Access AI Rule" section in `AI_PORTAL.md`. Row retained so the rejected reasoning is not rediscovered. |
| AIF-008 | MCC databuild session 2026-07-14 | workflow_pattern, continuity_plan | `docs/maintenance`, `AI_PORTAL.md`, dashboard | `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` | promoted | **Session-closeout convention.** Every session that changes lane state drops a dated `SESSION_CLOSEOUT_*.md` and indexes it in the dashboard Session Log. Template at `SESSION_CLOSEOUT_TEMPLATE.md`; rule folded into `AI_PORTAL.md` -> "Leave a Session Closeout". Turns AIF-006 from "update a pointer" into "leave a trail". |
| AIF-009 | MCC databuild session 2026-07-14 | agent_instruction, drift_or_risk | `labtalk/ai_portal` | `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` | promoted | **Local-access agent checklist.** The portal assumed hosted (propose-only) AI; a write-capable agent has a different failure mode (wedged the repo with a lock, swept 200 files with a loose `git add`, trusted a stale cache). Every checklist item is a mistake actually made this session. |
| AIF-010 | MCC databuild session 2026-07-14 | workflow_pattern | `AI_README.md` | `AI_README.md` -> "THIS FILE IS THE ONE FRONT DOOR" | promoted | **Single canonical entry order.** Resolved the overlap of ~5 onboarding docs and 15 mandatory first-reads into one ordered table (newest closeout first), everything else depth-on-demand. Per the AI Friendly Simplification Rule. Older list retained for continuity, marked superseded. |
| AIF-011 | MCC databuild session 2026-07-14 | drift_or_risk, proof_candidate | `docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md` | Runtime Findings table + `SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` | review-needed | **Four runtime findings** (`SETLMDB PHYSICAL`, `BUILDLMDB`/`SETLMDB` env mismatch, `SHOW TABLE` path misreport, bare `ASC`) moved out of the buried MCC README into the contract intake queue so source work surfaces them. Each awaits a maintainer decision through the source-mutation gate. |

## Intake Rules

- Add only distilled candidates, not entire conversations.
- Prefer existing destinations over new documents.
- Mark raw or weak material as `review-needed`.
- Mark obsolete material as `superseded` or `rejected` instead of letting it
  stay ambiguous.
- Keep evidence anchors explicit.
