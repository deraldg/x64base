---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260804-003
  recorded_at_utc: 2026-08-04T00:00:00Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: triggers phase-0 decisions signoff sheet
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 09bcaeb21266173bf6498dc6c0b69cfa5ee323d1
  authorization:
    requested_by: maintainer
    scope: provide a maintainer sign-off structure for Triggers Phase-0 decisions
  report:
    path: docs/maintenance/TRIGGERS_PHASE0_DECISIONS_SIGNOFF_V1.md
    kind: session_handoff
---

# Triggers Phase-0 -- Decisions A-G sign-off sheet (v1)

Maintainer sign-off structure for the Triggers PDLC lane (Q5 on the Agent Sync
page). This is a SKELETON: the hosted partner's Decisions A-G options memo slots
into the "Options" column; the maintainer fills "Decision" and "Signed".

## Hard gate

**Phase-1 trigger source is NO-GO until every row below is Signed AND the AIF is
claimed** (`python tools/coordination/session_coordinator.py claim-aif`). Docs
intake and decisioning are GO; source is not. This mirrors the AIF-043 -> AIF-046
Phase-0 doctrine: prove/settle before building.

## Known seam (grounds every decision)

- `cmd_trigger.cpp` is a design stub, no handler.
- Live surface is `SET POLLING`; `pre_poll`/`post_poll` are print-only.
- `replaceFieldStored` wires `index_hooks` (capture / apply_replace / detach) but
  does NOT notify a `cursor_hook`. The trigger fire-point is that missing notify.

## Decisions

Fill "Options" from the partner memo; maintainer sets "Decision" + "Signed".
(A-G are placeholders until the partner memo lands; rename each to its real
question. Do not invent decisions here.)

| # | Question (to be named from the partner memo) | Options (partner memo) | Decision (maintainer) | Signed (date) | Seam impact |
|---|---|---|---|---|---|
| A |  |  |  |  |  |
| B |  |  |  |  |  |
| C |  |  |  |  |  |
| D |  |  |  |  |  |
| E |  |  |  |  |  |
| F |  |  |  |  |  |
| G |  |  |  |  |  |

## Candidate question areas (prompts, not decisions)

To orient the partner memo. The real A-G come from the memo; these are only the
kinds of question a trigger feature must settle before code:

- Fire point: does the trigger fire at the `replaceFieldStored` / `index_hooks`
  seam via a new `cursor_hook` notify, or elsewhere?
- Trigger surface: new `TRIGGER` command vs. extending `SET POLLING`; `cmd_trigger`
  handler shape.
- Timing: pre vs. post mutation; ordering relative to index `apply_replace`.
- Scope: per-table / per-field / per-workspace registration and lifetime.
- Re-entrancy and recursion guard (a trigger that mutates and re-fires).
- Error model: trigger failure -> message-catalog `MessageId` + severity so
  `stop_on_error` governs it (AIF-036), not free-form strings.
- Rollback / transaction interaction (triggers under `TABLE BUFFER` / COMMIT).

## Sign-off record

- All A-G signed: [ ]  date: ______
- AIF claimed: [ ]  assigned: AIF-____  (replaces AIF-NEXT in the partner package)
- Phase-1 source unblocked: [ ]  date: ______

Until all three boxes are checked, the lane stays docs-only.
