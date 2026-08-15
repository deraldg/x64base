---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-GROK-003
  recorded_at_utc: 2026-08-15T13:25:00Z
  agent:
    provider: xAI
    product: Grok
    model: not_exposed
    access_mode: hosted_proposal
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: ea420f9b7
  authorization:
    requested_by: maintainer (Phase-0 locked; Phase-1 spike authorized to draft)
    scope: >
      Phase-1 spike brief and exercise package for AIF-112. No C++ src/**
      mutation. Dogfood x64base: ledger created/queried/locked only through
      DotTalk++ / x64base surfaces. pydottalk or CLI against a live instance.
      Reuse everything we can. Fossil remains considered-not-adopted unless
      this spike proves a required property the runtime surface cannot express.
  report:
    path: docs/maintenance/external_ai_intake/aif112_phase1_spike_2026-08-15/
    kind: review_needed_change_package
  primary_topics:
    - "AIF-112"
    - "document control"
    - "inventory"
    - "check-in check-out"
    - "Phase-1 spike"
    - "dogfood x64base"
---
# Review-Needed Change Package -- AIF-112 Phase-1 Spike

**Package id:** AIPR-20260815-GROK-003
**Date:** 2026-08-15
**Provider / product / model:** xAI / Grok / not_exposed
**Access mode:** remote (hosted_proposal; no write access to D:\code\ccode)
**Owner:** member.derald
**Assignee:** member.ai.grok.xai
**AIF:** AIF-112
**Status:** review-needed / spike definition; no C++ source mutation

## ai_report_audit envelope

- provider: xAI
- product: Grok
- model: not_exposed
- access_mode: remote
- AIF: **AIF-112**
- owning lifecycle / SDLC lane: Document Control / Inventory / Check-in-Check-out PDLC
- truth state: Phase-0 locked (ea420f9b7); Phase-1 spike defined
- proof state: unverified (spike not yet executed)
- risk class: low (no engine source change; dogfooded SQLite ledger prototype only)
- next gate: execute spike against live x64base; produce evidence note; decide whether runtime surface is sufficient or Fossil justification is warranted
- status: spike package ready for maintainer run / pydottalk exercise

## Locked constraints carried forward (must not drift)

- D1: ledger ONLY through x64base / DotTalk++ surfaces (never side-channel sqlite3)
- D7: pydottalk or CLI driving a live x64base instance
- Standing rule: reuse everything we can
- Fossil: considered-not-adopted unless this spike proves a required property the runtime surface cannot express
- No C++ src/** mutation in this spike
- Fence: Triggers, Identity, Tuple freeze, AIF-098, site-and-guard-hardening residue

## Package contents

- MANIFEST.md (this file)
- README.md
- notes/SPIKE_GOAL_AND_PROOF_BAR.md
- notes/LEDGER_SCHEMA_SKETCH.md
- notes/EXERCISE_OUTLINE.md
- notes/EVIDENCE_TEMPLATE.md
- notes/PROVISIONAL_DECISIONS_NEXT_GATE.md

## Baseline

- Branch: development
- Tip: ea420f9b7
- Phase-0 commit: ea420f9b7 (AIF-112 Phase-0 lock)

## Unresolved (spike will answer)

- Can the existing SQLITE command family + work areas express exclusive check-out cleanly?
- What minimal new tables (if any) are required, and can they be created through the runtime?
- Does a capsule-shaped reference fit without special-casing?
- Any property that forces reconsideration of Fossil?
