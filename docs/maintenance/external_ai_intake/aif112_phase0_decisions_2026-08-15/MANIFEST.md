# MANIFEST -- AIF-112 Phase-0 decisions packet

## ai_report_audit envelope

- report_id: AIPR-20260815-GROK-002
- ai_provider: xAI
- ai_product: Grok
- access_mode: remote (Outside-AI)
- registered_project_id: project.x64base.runtime
- authorization_scope: coordination + categorization only. NO source mutation proposed.
- report_path: docs/maintenance/external_ai_intake/aif112_phase0_decisions_2026-08-15/
- recorded_at_utc: 2026-08-15
- baseline_commit: development @ 23617ec67
- human_operated_tool: transcribed on-disk by member.ai.claude.cowork for member.derald

## Ticket

- AIF-112. Owner member.derald. Steward member.ai.grok.xai. Scribe member.ai.claude.cowork.
- Charter: `docs/maintenance/DOCUMENT_CONTROL_INVENTORY_CHECKINOUT_PDLC_LANE_V1.md` (Phase-0 flipped
  from PROVISIONAL to LOCKED with this packet).
- Acceptance package: `docs/maintenance/external_ai_intake/aif112_document_control_acceptance_2026-08-15/`
  (AIPR-20260815-GROK-001).

## Contents

- `PHASE0_DECISIONS.md` -- the signed D1-D8 decisions with the dogfood amendment (D1/D7).

## Provenance note

Placed in the established, audit-scanned landing zone `docs/maintenance/external_ai_intake/`, parallel
to the acceptance package. Grok's message referenced `artifacts/change_packages/aif112_phase0_decisions_2026-08-15/`
(also cited `notes/PHASE0_DECISIONS.md` on its side); the on-disk convention is this landing zone.
OPEN: the maintainer should pick one package location (external_ai_intake vs artifacts/change_packages)
so Grok and the on-disk scribe stop diverging; both AIF-112 packages currently live in external_ai_intake.
