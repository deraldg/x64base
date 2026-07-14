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

## Intake Rules

- Add only distilled candidates, not entire conversations.
- Prefer existing destinations over new documents.
- Mark raw or weak material as `review-needed`.
- Mark obsolete material as `superseded` or `rejected` instead of letting it
  stay ambiguous.
- Keep evidence anchors explicit.
