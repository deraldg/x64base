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

Maintainer sign-off for the Triggers PDLC lane (Q5 on the Agent Sync page).
Status: **SIGNED 2026-08-04** (AIF-087). A-G below carry the maintainer's chosen
options and rationale; the Phase-1 spike scope is authorized (patch-package only).

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

SIGNED by member.derald, 2026-08-04, against the hosted partner (Grok/xAI)
options memo (report AIPR-20260804-003/004), baseline development @ 2948d0b45.
AIF-087 claimed (member.derald, run COWORK-20260804-001, lane triggers-pdlc).

| # | Question | Chosen | Decision (maintainer) | Signed | Seam impact |
|---|---|---|---|---|---|
| A | Owning lifecycle | **A1** | DotTalk++/x64base engine SDLC primary. Triggers point back to the x64base runtime seam, not forward to LabTalk. Correct the stub `owning-lifecycle: labtalk_pdlc` -> x64base engine lifecycle (it already declares `project.x64base.runtime`). LabTalk teaching packaging is a deferred follow-on lane. | 2026-08-04 | none (ownership/lifecycle only) |
| B | Fire-point attachment | **B1** | Immediate `replaceFieldStored` path only for Phase-1. | 2026-08-04 | fire after a successful `index_hooks::apply_replace` in `replaceFieldStored`, via a dedicated per-area trigger hook -- NOT `cursor_hook` (single global slot owned by shell/TUI). |
| C | Body model | **C4** | C++ callback only in Phase-1; DotScript bodies deferred. | 2026-08-04 | handler is a C++ callback registered on the per-area hook. |
| D | Scope unit | **D2** | Per `DbArea`. | 2026-08-04 | matches `index_hooks::capture(*this)` per-area model; avoids the global-single `cursor_hook`. |
| E | TABLE BUFFER / ROLLBACK | **E1** | No fire on buffered edits yet (deferred). | 2026-08-04 | keeps `TABLE BUFFER`/COMMIT/ROLLBACK out of the seam; `dbarea.cpp` already excludes buffering from this direct-write path. |
| F | POLLING relationship | **F3** | POLLING stays diagnostics-only; TRIGGERS are a separate data-mutation mechanism. | 2026-08-04 | `pre_poll`/`post_poll` are command-boundary print stubs (`shell.cpp` dispatch), a different layer from the xbase mutation seam. Do not overload `SET POLLING`. |
| G | Proof shape | **G1** | C++ unit smoke for the spike. | 2026-08-04 | isolated smoke over the trigger hook at the `dbarea`/`index_hooks` level. |

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

- All A-G signed: [x]  date: 2026-08-04
- AIF claimed: [x]  assigned: AIF-087  (replaces AIF-NEXT in the partner package)
- Phase-1 source unblocked: [ ]  SCOPE authorized for a spike PATCH-PACKAGE only;
  tree `src/**` stays NO-GO until the maintainer reviews + cold-clone-builds and applies.

## Phase-1 spike -- authorized named-file scope (Source Mutation Gate)

Authorized for the hosted partner to draft as a PATCH-PACKAGE (proposal only; no
tree write; maintainer reviews + cold-clone builds before anything lands):

- `include/xbase/trigger_hooks.hpp`  (new) -- dedicated per-`DbArea` trigger hook
- `src/xbase/trigger_hooks.cpp`       (new)
- `src/xbase/dbarea.cpp`              (call site only: fire after successful `apply_replace`)
- `src/tests/<trigger smoke>`         (G1 C++ smoke)

Do NOT touch: `cursor_hook.*`, `cmd_polling` / `SET POLLING`, `pre_poll`/`post_poll`,
`cmd_trigger.cpp` (its `owning-lifecycle` marker fix and the user-facing `TRIGGER`
command are maintainer-side / a separate lane, per Decision A and the stub gate).
