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
| AIF-006 | Claude session 2026-07-13 (hosted, no repo access); re-evaluated 2026-07-14 with repo access | workflow_pattern, agent_instruction, drift_or_risk | `AI_PORTAL.md`, `AI_README.md`, `AI_ASSIMILATION_BOOK_V1.md` | `docs/agents/CURRENT_TARGET.md` drift, verified 2026-07-14 | anchored | **Closeout-updates-startup gate. MERGED 2026-07-14.** A session that changes lane state must update the AI-facing state document or explicitly decline with a reason. Evidence class: source-defined gate text; no automated runtime enforcement yet. |
| AIF-007 | Same session; withdrawn proposal | agent_instruction | — | `AI_PORTAL.md` Outside-AI Delivery Rule | rejected | Hosted-AI distinction was redundant. The real gap was local write-capable AI, addressed by the Local-Access AI Rule. |
| AIF-008 | MCC databuild session 2026-07-14 | workflow_pattern, continuity_plan | `docs/maintenance`, `AI_PORTAL.md`, dashboard | `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` | promoted | **Session-closeout convention.** State-changing sessions leave a dated closeout and add it to the dashboard Session Log. |
| AIF-009 | MCC databuild session 2026-07-14 | agent_instruction, drift_or_risk | `labtalk/ai_portal` | `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` | promoted | **Local-access agent checklist.** Write access is capability, not authorization; preserve work, avoid broad staging, and verify remote and runtime evidence. |
| AIF-010 | MCC databuild session 2026-07-14 | workflow_pattern | `AI_README.md` | `AI_README.md` -> "THIS FILE IS THE ONE FRONT DOOR" | promoted | **Single canonical entry order.** Newest closeout, current target, authority, local-access checklist where applicable, SDLC, source-mutation gate, and DotScript readiness. Other shelves are depth-on-demand. |
| AIF-011 | MCC databuild session 2026-07-14 | drift_or_risk, proof_candidate | `docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md` | Runtime Findings table + `SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` | review-needed | Four runtime findings moved from the MCC README into the contract intake queue for maintainer decision. |
| AIF-012 | Maintainer resume, 2026-07-14 | historical_note, continuity_plan, privacy_review | LabTalk campus (`labtalk/`) | `labtalk/LABTALK_DEVELOPER_PROFILE_v0.md` | routed — historical_review_needed; public-branch-exposed | Derived profile is absent from `main` but existed on a historical public branch. Keep outside `PROMOTE.manifest` and publication until reviewed. |
| AIF-013 | Maintainer unique-system discussion, 2026-07-14 | architectural_narrative, workflow_pattern, agent_instruction | Existing recursive co-development narrative | `labtalk/docs/co-development/recursive_coproject_model_v1.md` | anchored — design-intended | Human and AI participants share one evidence-backed task lens; portal context and proof gates constrain collaborators without granting authority. |
| AIF-014 | Maintainer build continuation, 2026-07-14 | proof_candidate, build_boundary, source_test | DotTalk++ xbase/xindex proof lane | `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`; `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md`; `bindings/pydottalk_xbase_contract_smoke.py` | development-runtime-proven; public edition publication pending | No-index distinction is executable in authoritative development. Physical DBF CRUD and provider profiles are proven there; attached-index mutation, public CDX/LMDB workflow, stale/collation rejection, and publication of the edition changeset remain open. |
| AIF-015 | Maintainer product/build separation request, 2026-07-14 | architecture_plan, product_boundary, packaging_risk, project_status_review | DotTalk++ SDLC + PLDC | `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` | implemented and proven in authoritative development; public source pending Path A | Engine capability and product edition are separate axes in development. Public `main` still exposes the older preset system; `BUILDING.md` is authoritative for what a fresh public clone contains. |
| AIF-016 | Cold-clone journey certification, 2026-07-15 | drift_or_risk, workflow_pattern, proof_candidate | `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md`; `BUILDING.md`; released `dottalkpp/scripts/mcc/*.ps1` + `launch-common.ps1` | `docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md` | promoted and published | Full public journey certified: clone -> `pro-md` build -> runtime staging -> MCC databuild -> ordered query. Location-honesty fixes published in `46e02159`; DotScript annotation corrected in `b9d48021`. |
| AIF-017 | Manual drift found during build-editions review, 2026-07-14 | drift_or_risk, manualgen_candidate | developer manual DEV-02 through manualgen | `BUILDING.md`; `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` | review-needed | DEV-02 predates the edition split. Do not hand-edit the combined manual; update the per-section source and regenerate only after the public edition system is published or clearly label development-only state. |

## Intake Rules

- Add only distilled candidates, not entire conversations.
- Prefer existing destinations over new documents.
- Mark raw or weak material as `review-needed`.
- Mark obsolete material as `superseded` or `rejected` instead of letting it stay ambiguous.
- Keep evidence anchors explicit.
- Keep IDs unique; never reuse an existing AIF identifier for a different item.
