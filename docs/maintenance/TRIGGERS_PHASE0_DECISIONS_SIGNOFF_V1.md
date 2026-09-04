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

## AMENDMENT 2026-09-03 -- what changed under this sheet

Signed 2026-08-04. Re-read against the tree today at the owner's direction
("change the specs to match today's reality and goals"). **The decisions are not
rewritten; they are dated and amended, because a sign-off sheet edited silently
stops being a record of what was signed.**

**Three things moved.**

1. **PHASE-1 LANDED THE SAME DAY IT WAS AUTHORIZED, AND THIS SHEET STILL SAYS
   IT DID NOT.** `include/xbase/trigger_hooks.hpp` and `src/xbase/trigger_hooks.cpp`
   exist (both 2026-08-04 16:10), and `src/xbase/dbarea.cpp:330` calls
   `trigger_hooks::fire_field_replace(*this, field1, rn)` after a successful
   `index_hooks::apply_replace`. **The seam is live.** The sign-off box below
   reads `Phase-1 source unblocked: [ ]` and is stale.

2. **THE SEAM IS LIVE AND UNREACHABLE.** `cmd_trigger.cpp` is still a design
   stub with no handler, so there is no user-facing `TRIGGER` command. Triggers
   today are a C++ callback an engine caller can register and nothing a user can
   attach. That is exactly what Decision A and the stub gate intended -- the
   command was always a separate lane -- but the two halves read as a
   contradiction to anyone checking, and they produced a real defect: the public
   ecosystem comparison table said **"Database triggers | Yes"** until it was
   corrected today. Someone saw the firing seam; someone else saw the stub. Both
   were looking at real things.

3. **DECISION E IS THE ONE TODAY INVALIDATES.** E1 deferred firing on buffered
   edits, and the rationale held at the time: `dbarea.cpp` excluded buffering
   from the direct-write path, so nothing important used it. **SQLsel P5 DML is
   now built on exactly that path** -- `sqlsel_statement.cpp:3178`, "typed SQL
   DML over the house table-buffer / WAL / lock machinery", with TBJ1 WAL and an
   explicit transaction state. So under E1 as signed, **a trigger does not fire
   for any SQL `INSERT` / `UPDATE` / `DELETE`.** A mechanism that fires for
   `REPLACE` and stays silent for `SQLSEL UPDATE` is a trap, not a deferral.

**And the delivery model changed.** The Phase-1 scope below authorizes a
PATCH-PACKAGE only, with `src/**` NO-GO, because the drafter was a hosted partner
(Grok/xAI) who could not write to the tree. Work is now done in-tree by an agent
with owner authorization. That gate describes a workflow that no longer exists;
it is retained below as history, not as a live constraint.

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

## Amended decisions -- 2026-09-03, review-needed

The 2026-08-04 signatures above stand as signed. These are the deltas today's
tree and today's goals require. **None is signed; each needs the maintainer.**

| # | As signed 2026-08-04 | State 2026-09-03 | Proposed amendment |
|---|---|---|---|
| A | x64base engine SDLC owns it | Unchanged and correct. The stub's `owning-lifecycle: labtalk_pdlc` marker is **still wrong** in `cmd_trigger.cpp` | No change to the decision; fix the stale marker when the stub becomes a handler |
| B | Fire at `replaceFieldStored` only | **Achieved** -- `dbarea.cpp:330` | Keep, and state the consequence plainly: this covers the direct write path and **nothing else** |
| C | C++ callback only; DotScript deferred | Unchanged | Keep for the engine seam. DotScript bodies belong with the user-facing command, not here |
| D | Per `DbArea` | Unchanged, but the axis grew: workspaces are co-resident since R128/R130 and SQLsel resolves names per workspace | Keep per-area, and state that a callback on an area in one workspace must not fire for a same-named table in another |
| E | **No fire on buffered edits** | **Invalidated.** SQLsel DML is built on TableBuffer + TBJ1 WAL, so as signed a trigger is silent for every SQL write | **Reopen.** The question is no longer "defer buffering" but "at which point in commit does a trigger fire, and can it refuse" -- and it must be answered before triggers are called real |
| F | POLLING stays diagnostics-only | Unchanged and correct | No change |
| G | C++ unit smoke | **Below today's bar.** The SQLsel lane established fail-closed validators, oracle comparison, and mutation-tested red | **Raise.** A trigger proof must show the trigger FIRED, fired ONCE, fired in the right ORDER against `index_hooks`, and **must be mutation-tested red** -- a trigger test that cannot fail is worth less than none |

## What "make triggers real" now means, in order

Recorded as scope, not as authorization.

1. **Decide E.** Firing point relative to buffer commit; whether a trigger may
   refuse a write; behaviour on `ROLLBACK`. Everything else is blocked on this,
   and it is a maintainer ruling rather than an implementation choice.
2. **Recursion and re-entrancy.** A trigger that writes re-enters
   `replaceFieldStored`. The signed sheet lists this under "candidate question
   areas" and it was never decided; the seam shipped without a guard.
3. **Error model.** The 2026-08-04 sheet already specified it: failure yields a
   message-catalog `MessageId` plus severity so `STOP_ON_ERROR` governs it
   (AIF-036), not free-form strings. Still owed.
4. **The user-facing `TRIGGER` command**, with its `@dottalk.usage` contract in
   the same commit as the handler -- the stub's own gate.
5. **Compose with `RULE`, do not duplicate it.** `RULE` is a declarative
   constraint checked by `VALIDATE`; a trigger is an imperative action on an
   event. If a trigger can refuse a write, the obvious first use is enforcing a
   declared `RULE` **at write time** -- which would close the gap between
   x64base's automatic domain integrity and its opt-in `CHECK` layer, and is the
   same hook entity and referential integrity would need.

## Sign-off record

- All A-G signed: [x]  date: 2026-08-04
- AIF claimed: [x]  assigned: AIF-087  (replaces AIF-NEXT in the partner package)
- Phase-1 source unblocked: [x]  **LANDED 2026-08-04** -- `trigger_hooks.{hpp,cpp}`
  plus the `dbarea.cpp:330` fire point. The patch-package restriction below is
  HISTORY: it described a hosted partner who could not write to the tree.
- Phase-2 (user-facing `TRIGGER`, buffered/transactional firing): **NOT authorized.**
  Blocked on the amended Decision E.

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
