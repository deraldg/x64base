# Lane assignment: Lane 1 write adapter (engine-bound half) -- coworker: Grok

**Status:** open assignment (review-needed). Owner: member.derald. Date 2026-08-08.
Coordinating agent: Claude (Cowork), run COWORK-20260807-005. Assignee coworker: **Grok**.
Delivered via pseudo-chat (BBS post on the agent board) + coordination quip.

## The split (by capability boundary)

The Frontal_Mem M2 consolidation is being built in two halves along the one line the sandbox
cannot cross -- running the engine.

- **DONE (Claude, engine-free, tested):** the judgment and the rendering.
  - `tools/memory/consolidate.py` -- the triage value function (five signals, hybrid
    propose/confirm, normalize-on-collect, cost-asymmetry bias). Tested, reproduces the
    hand-triage.
  - `tools/memory/promote.py` -- turns an owner-confirmed manifest into normalized, attributed
    `BBS POST` records + a runnable `.dts` script. Tested end to end.
- **YOURS (Grok, engine-bound):** the actual durable write and the store/UX seams that need a
  running `dottalkpp` / `dottalk_bbsd`.

## What to build

1. **Run and verify the attributed write.** Take `promote.py`'s `.dts` output and write the
   posts into the real store via `./datarun.ps1` as a logged-in member. Verify (thesis
   "trust the measurement"): each post exists with a real `author_id` (NEVER 0) and the
   source-lane marker; anon POST is denied (AIF-075).
2. **First-class source-lane `kind`.** Today the marker rides in the subject prefix
   (`[consolidated:<lane>]`). Add a real post `kind` field to the store (`bbs_store.cpp` /
   `post_new`) marking "consolidated-from-chat" with the lane, so recall can distinguish a
   promoted exchange from an authored post without string-parsing the subject
   (DESIGN_bbs_pseudochat_two_lanes.md, lane-boundary contract).
3. **Confirm UX (the one open decision).** Wire the hybrid owner-confirm step: either an
   interactive `PSEUDO PROMOTE ... CONFIRM`, or a `board.governance` approval reusing the
   SYSGRANT loop. The governance route is auditable and reuses existing machinery
   (PLAN_pseudochat_lane.md, M2 open decision). Name your choice.
4. **(Optional, if you take Lane 2 too):** the C++ `PSEUDO` command surface (M1) that buffers
   turns; it consumes the same `promote.py` records for its `PROMOTE`.

## Contract (the seam between the halves)

`promote.py render --manifest <confirmed.json>` emits `posts[]` and a `.dts`. Each post is:
`BBS POST <board> SUBJECT [consolidated:<lane>] <summary> BODY <normalized claim> (provenance ...)`.
Your write path consumes these verbatim. Do not re-open the judgment -- if a post is wrong, fix
the working-set/value-function inputs upstream, not the rendered post.

## Acceptance tests (repo idiom = datarun script + assertions; PLAN M2)

- Proposal requires owner confirm; on confirm the post exists with real `author_id` (not 0) and
  the source-lane marker; on decline nothing is written; buffer decays at session end.
- Normalization: a duplicate turn does not create a duplicate post; a contradicting turn is
  flagged/linked (`[reconsolidate vs ...]` is already emitted).

## Coordination rules (non-negotiable, CLAUDE.md / AIF-050 / AIF-075)

- **Claim a fresh AIF** (`session_coordinator.py claim-aif`); do NOT reuse AIF-052. Register the
  lane with the work (a lane with no intake row is abandoned).
- Attributed writes only -- `current_member()`, never author 0.
- Scoped per-path commits; `git status --short` between add and commit; pre-push gate.
- ASCII only; no em-dashes; `&&` is the DotTalk++ comment marker (BBS POST bodies must be
  comment-free). Use `./datarun.ps1`, not the raw exe. Stop the `DotTalkBBSD` task before
  rebuilding the daemon (it locks the exe -> LNK1104).

## Pointers

- `tools/memory/README.md`, `consolidate.py`, `promote.py` -- the built half.
- `docs/maintenance/DESIGN_bbs_pseudochat_two_lanes.md`, `PLAN_pseudochat_lane.md` -- the design
  and milestones (currently in the Frontal_Mem folder; promote if importing).
- `labtalk/ai_portal/FRONTAL_MEM_POINTER_V1.md` -- the root project, reachable via
  `trigger.persistent_memory`.
