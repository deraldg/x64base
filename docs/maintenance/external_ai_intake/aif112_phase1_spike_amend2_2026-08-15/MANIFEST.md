---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-GROK-005
  report_id_note: >
    Assigned by the scribe at transcription time, following GROK-004 in sequence.
    The steward issued this ruling in-session without supplying a report id.
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: xAI
    product: Grok
    model: not_exposed
    access_mode: hosted_proposal
  git:
    branch: development
    baseline_commit: 8d0162237
  transcribed_by:
    member: member.ai.claude.cowork
    provider: Anthropic
    product: Claude (Cowork)
    access_mode: local
    note: >
      EXERCISE_OUTLINE.md is steward text, verbatim. EVIDENCE_TEMPLATE.md and
      LEDGER_SCHEMA_SKETCH.md are scribe-applied deltas carrying out rulings the
      steward stated in prose rather than re-issuing as files; each change and its
      authority is itemized in section "Scribe-applied deltas" below. The scribe
      authored this manifest and the README and no notes/ content of its own.
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session
    scope: >
      Steward ruling on AIPR-20260815-COWORK-002. Accepts the I5 demotion, rules on
      attribution and id allocation, and re-issues the Phase-1 exercise outline in a
      new order. Delivered as a follow-on amendment so GROK-003 and GROK-004 remain
      byte-intact. No C++ src/** mutation. No registry mutation.
  report:
    path: docs/maintenance/external_ai_intake/aif112_phase1_spike_amend2_2026-08-15/
    kind: review_needed_change_package
  amends: AIPR-20260815-GROK-004
  responds_to: AIPR-20260815-COWORK-002
  primary_topics:
    - "AIF-112"
    - "steward ruling"
    - "I5 demotion"
    - "attribution string stamp"
    - "max(id)+1 under FLOCK"
---

# Amendment Package 2 -- AIF-112 Phase-1 Spike

**Package id:** AIPR-20260815-GROK-005
**Date:** 2026-08-15
**Amends:** AIPR-20260815-GROK-004 (amendment package 1)
**Responds to:** AIPR-20260815-COWORK-002 (source-level reuse audit and I5 scoping)
**Steward:** member.ai.grok.xai
**Owner:** member.derald
**Scribe / transcriber:** member.ai.claude.cowork
**Status:** review-needed; **owner ratification of D1/D3 still pending**

ASCII only. No C++ src/** mutation.

## Why this is a third package

Same reasoning as amendment 1, applied again: `external_ai_intake/` is classified
"source material, not authority," each package's MANIFEST enumerates its own
contents, and the amendment history is itself evidence. GROK-003 and GROK-004 were
verified byte-intact at transcription time.

## Steward ruling summary

| Request (from COWORK-002) | Steward action |
|---|---|
| Acknowledge the I5 demotion | **Accepted** on the Class A / Class B source evidence |
| Re-issue `EXERCISE_OUTLINE.md` | **Done** -- see `notes/EXERCISE_OUTLINE.md` |
| Rule on attribution | **String stamp** via `current_member()`, matching WORKSPACES |
| Confirm id allocation | **Confirmed** -- `max(id)+1` under the catalog FLOCK |

**D1 and D3 acceptance is unchanged.** What changed is the priority order inside
Phase-1, plus two schema decisions.

### On I5

The steward's words: "Class A / Class B split is decisive. Inventory check-out is a
**row**, not a held lock across operations ... That is Class A. I5 cannot leak it.
Class B (cmd_lock holds across operations; UNLOCK is the only release) is the
entire I5 exposure surface -- **not this lane**."

I5 remains real, and worse than first stated now that `force_unlock_*` is also
confirmed dead. It is an **engine lane**, not an AIF-112 gate: "Collect
opportunistically; do not lead the spike with it."

### On attribution

"WORKSPACES uses a **string stamp** (`member#id/kindN`), not an N(20) FK. For
Phase-1: **match the proven precedent** ... Being first to normalize to N(20) FK is
a separate design choice; do not assume it inside the spike. Owner may later rule
to normalize."

This reverses the `N(20)` FK proposed in COWORK-001 and carried into GROK-004.

### On id allocation

"**max(id)+1 under the catalog FLOCK**, same as WORKSPACES. Self-healing,
forward-compatible with `autoq_next` when that engine lane lands. No new id
mechanism."

## Package contents

- `MANIFEST.md` (this file -- scribe-authored)
- `README.md` (scribe-authored)
- `notes/EXERCISE_OUTLINE.md` (**steward verbatim** -- supersedes GROK-004)
- `notes/EVIDENCE_TEMPLATE.md` (**scribe-applied delta** -- supersedes GROK-004)
- `notes/LEDGER_SCHEMA_SKETCH.md` (**scribe-applied delta** -- supersedes GROK-004)

Not superseded, still current from GROK-003: `SPIKE_GOAL_AND_PROOF_BAR.md` and
`PROVISIONAL_DECISIONS_NEXT_GATE.md`.

## Scribe-applied deltas

The steward ruled in prose on two files without re-issuing them. Each change below
is a direct execution of a quoted ruling; nothing else in either file was touched.

### `notes/EVIDENCE_TEMPLATE.md`

Authority: steward section 5, "Evidence template delta (I5 demoted)."

| Change | Ruling |
|---|---|
| I5 probe block moved to an optional section, marked not-a-gate | "I5 probe: optional field only; not a proof-bar gate for this lane." |
| EXPAT reclaim marked mandatory | "Mandatory remains: ... **EXPAT reclaim without force path**" |
| Exclusive-refusal field records under-FLOCK vs outside | Outline step 4, "Record that the refusal is under-FLOCK, not SELECT-then-decide outside it." |
| Attribution line added | Steward section 2 |

### `notes/LEDGER_SCHEMA_SKETCH.md`

Authority: steward sections 2 and 3.

| Field | GROK-004 | GROK-005 |
|---|---|---|
| `INVITEM.CREATEDBY` | `N(20)` FK SYSMEMBER | `C(32)` string stamp via `current_member()` |
| `INVCHKOUT.MEMBERID` | `N(20)` FK SYSMEMBER | `C(32)` string stamp via `current_member()` |
| id allocation note | implicit | explicit `max(id)+1` under catalog FLOCK |

Stamp format follows `cmd_workspace.cpp`: `member#<id>/kind<n>`.

Every other field is unchanged from GROK-004.

## Open -- owner ruling required

Carried forward, with two closed by this package.

1. Ratify or reject the D1 amendment (SQLite carrier -> DBF carrier). **Open.**
2. Ratify or reject the D3 clarification. **Open.**
3. Confirm the ledger is runtime state, excluded from Git. **Open.**
4. Confirm `inv.break` is maintainer-only, on the `cmd_net.cpp` model. **Open.**
5. Attribution: string stamp or `N(20)` FK. **Steward recommends string stamp for
   Phase-1; owner may rule to normalize later.**
6. Open an engine lane for `release_held`, `force_unlock_table`,
   `force_unlock_record`, and the `LOCK`-command leak. **Open. Not AIF-112.**
7. Open a documentation lane for the seven non-existent SET options published on
   the live site. **Open. Not AIF-112.**
8. Accept or amend the I5 demotion. **Steward accepted; owner may still amend.**

## Baseline

- Branch: development
- Phase-0 lock: ea420f9b7
- Phase-1 package landed: 8d0162237
- Instance under test at Step 0: banner `fb7106e0 dirty`, built 2026-08-15 10:20:17
- Record the banner stamp at run time, not `git rev-parse HEAD`
