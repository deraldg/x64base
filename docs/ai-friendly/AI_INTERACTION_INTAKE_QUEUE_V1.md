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

## Intake Rules

- Add only distilled candidates, not entire conversations.
- Prefer existing destinations over new documents.
- Mark raw or weak material as `review-needed`.
- Mark obsolete material as `superseded` or `rejected` instead of letting it
  stay ambiguous.
- Keep evidence anchors explicit.
