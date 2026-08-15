---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-GROK-004
  report_id_note: >
    Assigned by the scribe at transcription time. The steward issued this ruling
    in-session without supplying a report id; the id follows GROK-003 in
    sequence and is recorded here so the amendment is citable.
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: xAI
    product: Grok
    model: not_exposed
    access_mode: remote
  transcribed_by:
    member: member.ai.claude.cowork
    provider: Anthropic
    product: Claude (Cowork)
    access_mode: local
    note: >
      Steward text transcribed verbatim. The scribe added this manifest and the
      README; it authored none of the notes/ content.
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session
    scope: >
      Steward ruling on AIPR-20260815-COWORK-001. Accepts the D1/D3 amendments
      and re-issues three Phase-1 notes files DBF-native. Delivered as a
      follow-on amendment package so that AIPR-20260815-GROK-003 remains
      byte-intact. No C++ src/** mutation. No registry mutation.
  report:
    path: docs/maintenance/external_ai_intake/aif112_phase1_spike_amend1_2026-08-15/
    kind: review_needed_change_package
  amends: AIPR-20260815-GROK-003
  responds_to: AIPR-20260815-COWORK-001
  primary_topics:
    - "AIF-112"
    - "steward ruling"
    - "DBF carrier"
    - "I5 lock-release defect"
    - "EXPAT lease"
    - "check-in check-out"
---

# Amendment Package 1 -- AIF-112 Phase-1 Spike

**Package id:** AIPR-20260815-GROK-004
**Date:** 2026-08-15
**Amends:** AIPR-20260815-GROK-003 (Phase-1 spike package)
**Responds to:** AIPR-20260815-COWORK-001 (prior-art inventory and D1/D3 revision)
**Steward:** member.ai.grok.xai
**Owner:** member.derald
**Scribe / transcriber:** member.ai.claude.cowork
**Status:** review-needed; steward has accepted, **owner ruling still pending**

ASCII only. No C++ src/** mutation.

## Why this is a separate package

The steward offered a choice: rewrite the original package files, or issue a
follow-on amendment. This tree takes the second option, because:

1. `AI_SYSTEMS_CROSSWALK_V1.md` classifies `docs/maintenance/external_ai_intake/`
   as an "active landing zone ... source material, not authority." Preserved
   source material should stay preserved.
2. The GROK-003 `MANIFEST.md` enumerates its package contents explicitly.
   Editing files in place, or adding files to that directory, puts the manifest
   out of agreement with the tree.
3. The amendment history is itself evidence. Keeping GROK-003 and GROK-004 side
   by side records that the carrier decision changed, when, and on what
   evidence -- which the append-only doctrine used everywhere else in this
   project would ask for.

`aif112_phase1_spike_2026-08-15/` is unmodified and was verified byte-intact at
transcription time.

## Steward ruling summary

D1/D3 amendments **accepted** on prior-art evidence, on five grounds recorded by
the steward:

1. Reuse-first was already in the original sketch; the steward could not execute
   the inspection, and the missing input has now been supplied (WORKSPACES,
   SYSGRANT, FLOCK, session_coordinator checkin/checkout, engine LOCK/UNLOCK).
2. Dogfood is better served by the native DBF carrier; a SQLite side ledger
   would be a parallel path, not dogfood.
3. I5 is a real blocker invisible on the SQLite path -- a green SQLite proof bar
   that never touches `xbase_locks` would leave the deadlock mode undiscovered.
4. House naming: `INV_CHECKOUT` at 12 chars was out of convention;
   `INVITEM` / `INVCHKOUT` are correct.
5. `EXPAT` lease reuses the SYSGRANT pattern and mitigates I5 without an engine
   change in Phase-1.

## Amended decisions

| ID | Amended value |
|----|---------------|
| D1 | In-tree DBF catalogs under `data/metadata/inventory/`, created / queried / locked ONLY through x64base / DotTalk++ surfaces, following WORKSPACES and identity-catalog patterns. Never side-channel sqlite3. SQLite retained as verification oracle only. |
| D3 | Recovery clause promoted to the Phase-1 goal, scoped against I5. Phase-1 determines whether stale/abandoned recovery is reachable without engine change, or requires wiring `release_held` (separate lane / authorization). |
| D7 | Read as: CLI for LOCK/UNLOCK; pydottalk available for record-level assertions only. pydottalk is not the command shell. |

**Unchanged:** reuse-first, Fossil considered-not-adopted, no C++ `src/**` in
this spike, the fence, proof bar core, status vocabulary, P1-P7.

## Package contents

- `MANIFEST.md` (this file -- scribe-authored)
- `README.md` (scribe-authored)
- `notes/LEDGER_SCHEMA_SKETCH.md` (steward, verbatim -- supersedes GROK-003)
- `notes/EXERCISE_OUTLINE.md` (steward, verbatim -- supersedes GROK-003)
- `notes/EVIDENCE_TEMPLATE.md` (steward, verbatim -- supersedes GROK-003)

Files in GROK-003 not superseded here remain current: `SPIKE_GOAL_AND_PROOF_BAR.md`
and `PROVISIONAL_DECISIONS_NEXT_GATE.md`.

## Baseline

- Branch: development
- Phase-0 lock: ea420f9b7
- Phase-1 package landed: 8d0162237
- Tip at transcription: record at run time

## Open -- owner ruling required

1. Ratify or reject the D1 amendment (SQLite carrier -> DBF carrier).
2. Ratify or reject the D3 clarification.
3. Confirm the ledger is runtime state and excluded from Git.
4. If the I5 probe reproduces: authorize a separate lane for wiring
   `release_held` into area close, or accept `EXPAT` as the Phase-1 mitigation
   and defer the engine fix.
5. Confirm `inv.break` is maintainer-only.
6. Decide whether AIF-112 state is published to the AI Agent Sync page, and in
   what redacted form. See README section "Delivery note."
